from fastapi import APIRouter, UploadFile, File, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

from app.services.firmware_service import FirmwareService
from app.services.signature_service import SignatureService
from app.services.publisher_service import PublisherService
from app.utils.directories import sha256_file, get_latest_version
from fastapi.responses import HTMLResponse


router = APIRouter(prefix="/firmwares", tags=["firmwares"])



@router.post("/upload/init/{device}")
async def init_upload(device: str, file_size: int):
    """
    Start a resumable firmware upload session (CI / Admin system).
    """
    return await FirmwareService.init_upload_session(device, file_size)


@router.post("/upload/chunk/{device}")
async def upload_chunk(
    device: str,
    session_id: str,
    chunk_index: int,
    data: bytes = File(...),
):
    """
    Upload firmware chunk (server-side ingestion system).
    NOT used by IoT devices.
    """
    try:
        return await FirmwareService.write_chunk(
            device=device,
            session_id=session_id,
            chunk_index=chunk_index,
            data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload/complete/{device}")
async def complete_upload(
    device: str,
    session_id: str,
    background_tasks: BackgroundTasks,
):
    """
    Finalize firmware upload and publish update event.
    """

    try:
        result = await FirmwareService.finalize_upload(device, session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # async event publish (RabbitMQ)
    if background_tasks:
        background_tasks.add_task(
            PublisherService.publish_update,
            device,
            result["version"],
        )

    return result



@router.get("/fw/{device}/{filename}")
async def get_firmware(device: str, filename: str):

    file_path = FirmwareService.get_file(device, filename)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Firmware not found")

    sig_path = file_path.with_suffix(".bin.sig")
    if not sig_path.exists():
        raise HTTPException(status_code=404, detail="Signature missing")

    signature_bytes = sig_path.read_bytes()

    # safe version extraction
    version = filename.replace("v", "").replace(".bin", "")

    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=filename,
        headers={
            "X-Signature": SignatureService.encode_signature(signature_bytes),
            "X-Signature-Algorithm": "ecdsa-sha256",
            "X-SHA256": sha256_file(file_path),
            "X-Firmware-Version": version,
        },
    )



@router.get("/ota/latest")
async def latest_manifest(device: str, request: Request):

    version = get_latest_version(device)
    print(f"Latest firmware for {device}: v{version}")
    if version <= 0:
        raise HTTPException(status_code=404, detail="No firmware available")

    file_path = FirmwareService.get_file(device, f"v{version}.bin")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Firmware file missing")

    return JSONResponse({
        "device": device,
        "version": version,
        "firmware_url": str(
            request.url_for(
                "get_firmware",
                device=device,
                filename=f"v{version}.bin",
            )
        ),
        "sha256": sha256_file(file_path),
        "size": file_path.stat().st_size,
    })



@router.get("/files/{device}")
async def list_firmware(device: str):
    return {
        "device": device,
        "files": await FirmwareService.list_files(device),
    }

@router.get("/ui/upload", response_class=HTMLResponse)
async def upload_ui():

    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>OTA Upload (Resume + Pause)</title>

    <style>
        body {
            font-family: Arial;
            max-width: 600px;
            margin: auto;
            padding: 30px;
        }

        input, button {
            padding: 10px;
            margin-top: 10px;
            width: 100%;
        }

        .progress {
            width: 100%;
            background: #eee;
            height: 20px;
            margin-top: 15px;
            border-radius: 10px;
            overflow: hidden;
        }

        .bar {
            height: 100%;
            width: 0%;
            background: green;
            transition: 0.2s;
        }

        button {
            cursor: pointer;
        }
    </style>
</head>

<body>

<h2>OTA Firmware Upload (Pause / Resume)</h2>

<input id="device" placeholder="Device name" />
<input type="file" id="fileInput" />

<button onclick="startUpload()">Start</button>
<button onclick="pauseUpload()">Pause</button>
<button onclick="resumeUpload()">Resume</button>
<button onclick="simulateCrash()">Simulate Crash</button>

<div class="progress">
    <div class="bar" id="bar"></div>
</div>

<p id="status"></p>

<script>

const CHUNK_SIZE = 512 * 1024;

let file = null;
let sessionId = null;
let device = null;

let uploaded = 0;
let index = 0;
let isPaused = false;
let isUploading = false;


// ================= START =================
async function startUpload() {

    device = document.getElementById("device").value;
    file = document.getElementById("fileInput").files[0];

    if (!device || !file) {
        alert("Missing input");
        return;
    }

    isPaused = false;
    isUploading = true;

    document.getElementById("status").innerText = "Creating session...";

    const res = await fetch(`/firmwares/upload/init/${device}?file_size=${file.size}`, {
        method: "POST"
    });

    const data = await res.json();
    sessionId = data.session_id;

    uploaded = data.offset || 0;
    index = Math.floor(uploaded / CHUNK_SIZE);

    localStorage.setItem("sessionId", sessionId);
    localStorage.setItem("uploaded", uploaded);

    document.getElementById("status").innerText = "Uploading...";

    uploadLoop();
}


// ================= UPLOAD LOOP =================
async function uploadLoop() {

    while (uploaded < file.size) {

        if (isPaused) {
            document.getElementById("status").innerText = "Paused ⏸";
            return;
        }

        const chunk = file.slice(uploaded, uploaded + CHUNK_SIZE);

        const form = new FormData();
        form.append("data", chunk);

        try {
            const res = await fetch(
                `/firmwares/upload/chunk/${device}?session_id=${sessionId}&chunk_index=${index}`,
                {
                    method: "POST",
                    body: form
                }
            );

            if (!res.ok) throw new Error("Upload failed");

            uploaded += CHUNK_SIZE;
            index++;

            localStorage.setItem("uploaded", uploaded);

            updateBar();

            // simulate slow network
            await new Promise(r => setTimeout(r, 300));

        } catch (err) {
            console.log("Retry...");
            await new Promise(r => setTimeout(r, 1000));
        }
    }

    finalize();
}


// ================= FINALIZE =================
async function finalize() {

    document.getElementById("status").innerText = "Finalizing...";

    await fetch(
        `/firmwares/upload/complete/${device}?session_id=${sessionId}`,
        { method: "POST" }
    );

    document.getElementById("status").innerText = "Done ✔";
}


// ================= PAUSE =================
function pauseUpload() {
    isPaused = true;
}


// ================= RESUME =================
function resumeUpload() {

    if (!file) return;

    isPaused = false;

    sessionId = localStorage.getItem("sessionId");
    uploaded = parseInt(localStorage.getItem("uploaded") || "0");
    index = Math.floor(uploaded / CHUNK_SIZE);

    document.getElementById("status").innerText = "Resuming...";

    uploadLoop();
}


// ================= SIMULATE CRASH =================
function simulateCrash() {

    // kill process locally (simulated)
    isPaused = true;
    isUploading = false;

    document.getElementById("status").innerText = "CRASHED 💥 (reload to resume)";
}


// ================= PROGRESS BAR =================
function updateBar() {

    const percent = Math.min((uploaded / file.size) * 100, 100);
    document.getElementById("bar").style.width = percent + "%";
}

</script>

</body>
</html>
""")