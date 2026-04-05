# backend/webrtc.py
import asyncio
import os
import time
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay, MediaRecorder
from event_processor import process_and_ingest_event
from vision import process_video_track, motion_state

os.makedirs("motion_clips", exist_ok=True)

relay = MediaRelay()
pcs = set()

active_tracks = {"video": None, "audio": None}
recorder = None
current_filename = None  # <--- Add this to track the filename

async def start_recording():
    global recorder, current_filename
    if active_tracks["video"] and active_tracks["audio"] and recorder is None:
        current_filename = f"motion_clips/event_{int(time.time())}.mp4"
        print(f"🎥 Starting new event recording: {current_filename}")
        
        recorder = MediaRecorder(current_filename)
        recorder.addTrack(relay.subscribe(active_tracks["audio"]))
        recorder.addTrack(relay.subscribe(active_tracks["video"]))
        
        await recorder.start()
        return current_filename
    return None

async def stop_recording():
    global recorder, current_filename
    if recorder is not None:
        print(f"⏹️ Motion ended. Saving {current_filename} to disk...")
        await recorder.stop()
        
        saved_file = current_filename
        
        # Reset the globals for the next motion event
        recorder = None
        current_filename = None
        
        print("✅ Ready for AI Ingestion. Firing background task...")
        # Fire and forget the AI ingestion so it doesn't block the live stream
        asyncio.get_event_loop().run_in_executor(None, process_and_ingest_event, saved_file)
async def recorder_watcher_loop():
    """Continuously checks the motion state from vision.py to start/stop recording."""
    is_recording = False
    while True:
        await asyncio.sleep(0.5) # Check state twice a second
        
        if motion_state["is_active"] and not is_recording:
            await start_recording()
            is_recording = True
            
        elif not motion_state["is_active"] and is_recording:
            await stop_recording()
            is_recording = False

async def process_offer(offer_sdp: str, offer_type: str):
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state is {pc.connectionState}")
        if pc.connectionState in ["failed", "closed"]:
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        print(f"Received {track.kind} track from frontend.")
        
        if track.kind == "audio":
            active_tracks["audio"] = track
            
        elif track.kind == "video":
            active_tracks["video"] = track
            
            # Send a copy of the video directly to OpenCV for analysis
            video_copy = relay.subscribe(track)
            asyncio.create_task(process_video_track(video_copy))
            
            # Start the background loop that manages the .mp4 file saving
            asyncio.create_task(recorder_watcher_loop())

    # WebRTC Handshake
    offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}