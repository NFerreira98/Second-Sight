# backend/webrtc.py
import json
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from vision import process_video_track

# Store active connections
pcs = set()

async def process_offer(offer_sdp: str, offer_type: str):
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed" or pc.connectionState == "closed":
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        print(f"Received {track.kind} track from frontend.")
        if track.kind == "video":
            # Fire and forget the OpenCV processing loop as a background task
            asyncio.create_task(process_video_track(track))

    offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}