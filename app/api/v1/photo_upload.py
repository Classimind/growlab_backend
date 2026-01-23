from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
import os
from datetime import datetime

app = APIRouter()

# Folder to save uploaded photos
UPLOAD_FOLDER = "uploaded_photos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload_photo/")
async def upload_photo(file: UploadFile = File(...)):
    try:
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{timestamp}{file_ext}"

        file_path = os.path.join(UPLOAD_FOLDER, filename)
        # Save file to server
        with open(file_path, "wb") as f:
            f.write(await file.read())

        return JSONResponse({"status": "success", "filename": filename})
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

# Optional: list all uploaded photos
@app.get("/photos/")
async def list_photos():
    files = os.listdir(UPLOAD_FOLDER)
    return {"photos": files}
