# backend/webrtc.py
import json
from aiortc import RTCPeerConnection, RTCSessionDescription

# Store active connections
pcs = set()

async def process_offer(offer_sdp: str, offer_type: str):
    """
    Takes the connection offer from the frontend browser,
    sets up the video receiver, and returns an answer.
    """
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
        # Later, we will pass this track to OpenCV for motion detection
        if track.kind == "video":
            pass 

    # Accept the browser's offer
    offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer)

    # Create an answer to send back to the browser
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}