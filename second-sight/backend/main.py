from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from deeplake import Client
import os
import json
from dotenv import load_dotenv
from webrtc import process_offer
import certifi

# Fix for Mac Python SSL Certificate errors
os.environ["SSL_CERT_FILE"] = certifi.where()

load_dotenv()

# The new DeepLake Managed SDK expects the environment variable to be named 'DEEPLAKE_API_KEY'.
# We will map your existing DEEPLAKE_TOKEN to it automatically so you don't have to change your .env file.
if "DEEPLAKE_TOKEN" in os.environ and "DEEPLAKE_API_KEY" not in os.environ:
    os.environ["DEEPLAKE_API_KEY"] = os.environ["DEEPLAKE_TOKEN"]

app = FastAPI(title="Second Sight API")

# We declare the client globally so other parts of the backend can use it later to save video frames
dl_client = None

def init_db():
    """
    Initializes the new DeepLake Managed Client.
    Because the new SDK infers the schema dynamically upon data ingestion, 
    we just verify the connection here rather than explicitly creating empty tensors.
    """
    global dl_client
    try:
        print("Connecting to DeepLake Managed Service...")
        dl_client = Client()
        
        # We test the connection by asking the database for a list of existing tables
        tables = dl_client.list_tables()
        print(f"Successfully connected to DeepLake! Existing tables: {tables}")
    except Exception as e:
        print(f"Failed to connect to DeepLake Workspace. Error: {e}")

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.websocket("/ws/video")
async def websocket_video_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for WebRTC signaling.
    The Next.js camera page connects here to establish the video stream.
    """
    await websocket.accept()
    try:
        # Wait for the frontend to send an SDP offer
        data = await websocket.receive_text()
        offer_dict = json.loads(data)
        
        # Process the offer and generate an answer using aiortc (from webrtc.py)
        answer_dict = await process_offer(offer_dict["sdp"], offer_dict["type"])
        
        # Send the acknowledgment answer back to the frontend
        await websocket.send_text(json.dumps(answer_dict))
        
        # Keep connection open for the lifetime of the stream
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        print("WebRTC Signaling WebSocket disconnected")