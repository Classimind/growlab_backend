from fastapi import APIRouter, File, UploadFile, Request, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime
import uuid

app = APIRouter()

# -----------------------
# Configuration
# -----------------------

UPLOAD_FOLDER = Path("uploaded_photos")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_MB = 10

# -----------------------
# Helpers
# -----------------------

def validate_extension(filename: str):
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {ext}"
        )
    return ext


def generate_filename(ext: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]
    return f"{timestamp}_{uid}{ext}"

# -----------------------
# Routes
# -----------------------

@app.post("/upload_photo/")
async def upload_photo(request: Request, file: UploadFile = File(...)):
    try:
        ext = validate_extension(file.filename)

        contents = await file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail="File too large"
            )

        filename = generate_filename(ext)
        file_path = UPLOAD_FOLDER / filename

        # Atomic write
        tmp_path = file_path.with_suffix(".tmp")
        with open(tmp_path, "wb") as f:
            f.write(contents)
        tmp_path.rename(file_path)

        image_url = str(request.base_url) + f"images/{filename}"

        return {
            "status": "success",
            "filename": filename,
            "url": image_url,
            "size_kb": round(len(contents) / 1024, 2)
        }

    except HTTPException:
        raise

    except Exception as e:
        return JSONResponse(
            {"status": "error", "detail": str(e)},
            status_code=500
        )


@app.get("/photos/")
async def list_photos(request: Request):
    base_url = str(request.base_url)
    photos = []

    for file in sorted(UPLOAD_FOLDER.iterdir()):
        if file.is_file():
            photos.append({
                "filename": file.name,
                "url": base_url + f"images/{file.name}",
                "size_kb": round(file.stat().st_size / 1024, 2)
            })

    return {"count": len(photos), "photos": photos}
