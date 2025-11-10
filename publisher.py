import asyncio
import logging
import os
import sys
import cv2
from livekit import api, rtc
from dotenv import load_dotenv


# --- Video settings ---
WIDTH = 1280
HEIGHT = 720
FPS = 30

load_dotenv()
logger = logging.getLogger(__name__)

async def main(room: rtc.Room, room_name: str):
    # --- Generate AccessToken ---
    token = (
        api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))
        .with_identity("python-pub")
        .with_name("Safal Shrestha")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )
    print("Access Token:", token)

    url = "ws://livekit.safalstha.com.np:9881"  # replace with your LiveKit server URL
    logger.info("Connecting to %s", url)

    try:
        await room.connect(url, token)
        logger.info("Connected to room %s", room.name)
    except rtc.ConnectError as e:
        logger.error("Failed to connect: %s", e)
        return

    # --- Video Source and Track ---
    video_source = rtc.VideoSource(WIDTH, HEIGHT)
    video_track = rtc.LocalVideoTrack.create_video_track("webcam", video_source)

    video_options = rtc.TrackPublishOptions(
        source=rtc.TrackSource.SOURCE_CAMERA,
        video_encoding=rtc.VideoEncoding(
            max_framerate=FPS,
            max_bitrate=50_000_000  # higher bitrate for quality
        ),
        video_codec=rtc.VideoCodec.H264
    )

    await room.local_participant.publish_track(video_track, video_options)
    logger.info("Publishing webcam video...")

    # --- OpenCV capture ---
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    async def _stream():
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            # Convert BGR → RGBA
            frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            vf = rtc.VideoFrame(
                WIDTH, HEIGHT, rtc.VideoBufferType.RGBA, frame_rgba.tobytes()
            )
            video_source.capture_frame(vf)
            await asyncio.sleep(1 / FPS)

    await _stream()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.FileHandler("video_publish.log"), logging.StreamHandler()],
    )

    if len(sys.argv) != 2:
        print("Usage: python livekit_server_test.py <room-name>")
        sys.exit(1)

    room_name = sys.argv[1]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    room = rtc.Room(loop=loop)

    async def cleanup():
        await room.disconnect()
        loop.stop()

    try:
        loop.create_task(main(room, room_name))
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        loop.run_until_complete(cleanup())
    finally:
        loop.close()
