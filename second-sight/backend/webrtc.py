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
current_filename = None 

async def start_recording():
    global recorder, current_filename
    if active_tracks["video"] and active_tracks["audio"] and recorder is None:
        current_filename = f"motion_clips/event_{int(time.time())}.mp4"
        print(f"🎥 Starting new event recording: {current_filename}")
        
        try:
            recorder = MediaRecorder(current_filename)
            recorder.addTrack(relay.subscribe(active_tracks["audio"]))
            recorder.addTrack(relay.subscribe(active_tracks["video"]))
            await recorder.start()
        except Exception as e:
            print(f"Failed to start recorder: {e}")
            recorder = None
        
        return current_filename
    return None

async def stop_recording():
    global recorder, current_filename
    if recorder is not None:
        saved_file = current_filename
        print(f"⏹️ Motion ended. Finalizing {saved_file} to disk...")
        
        try:
            # Tell aiortc to finish writing the .mp4 wrapper
            await recorder.stop()
        except ValueError:
            # Known aiortc Mac bug if connection drops unexpectedly. Safe to ignore.
            pass
        except Exception as e:
            print(f"Warning on record stop: {e}")
            
        recorder = None
        current_filename = None
        
        print("✅ Event fully recorded. Triggering AI Ingestion...")
        # Fire and forget the AI ingestion so it doesn't block the video stream
        asyncio.get_event_loop().run_in_executor(None, process_and_ingest_event, saved_file)

async def recorder_watcher_loop():
    """Continuously checks the motion state from vision.py to start/stop recording."""
    is_recording = False
    while True:
        await asyncio.sleep(0.5) 
        
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
        global active_tracks
        print(f"Received {track.kind}")
        
        if track.kind == "audio":
            active_tracks["audio"] = track
            
        elif track.kind == "video":
            active_tracks["video"] = track
            
            # Send a copy of the video directly to OpenCV for motion analysis
            video_copy = relay.subscribe(track)
            asyncio.create_task(process_video_track(video_copy))
            
            # Start the background loop that manages the .mp4 file saving based on motion
            asyncio.create_task(recorder_watcher_loop())

    # Accept the browser's offer
    offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer)

    # Create an answer to send back to the browser
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}