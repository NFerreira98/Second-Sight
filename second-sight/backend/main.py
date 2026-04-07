# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from deeplake import Client
import numpy as np
import asyncio
import os
import json
import certifi
import time
from dotenv import load_dotenv
from datetime import datetime
from vision import latest_frames

# Import local modules
from webrtc import process_offer
from gemini_client import generate_text_embedding

# Fix for Mac Python SSL Certificate errors
os.environ["SSL_CERT_FILE"] = certifi.where()

load_dotenv()

# Dictionary to track active cameras
active_cameras = {}

# Define the app
app = FastAPI(title="Second Sight API")

# Completely permissive CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "ws://localhost:3000",
        "ws://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the motion clips folder statically
os.makedirs("motion_clips", exist_ok=True)
app.mount("/motion_clips", StaticFiles(directory="motion_clips"), name="motion_clips")

dl_client = None

# Pydantic model for the search request
class SearchQuery(BaseModel):
    text: str
    limit: int = 5

# Add this model near your SearchQuery class
class SetupCredentials(BaseModel):
    gemini_key: str
    deeplake_key: str
    deeplake_org: str

@app.get("/system/status")
def get_system_status():
    """Checks if the user has configured their API keys yet."""
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_deeplake = bool(os.getenv("DEEPLAKE_API_KEY"))
    has_org = bool(os.getenv("DEEPLAKE_ORG_ID"))
    
    return {
        "needs_setup": not (has_gemini and has_deeplake and has_org)
    }

@app.post("/system/setup")
def save_system_setup(creds: SetupCredentials):
    """Saves the user's API keys to the local .env file."""
    env_content = f"""GEMINI_API_KEY="{creds.gemini_key.strip()}"
DEEPLAKE_API_KEY="{creds.deeplake_key.strip()}"
DEEPLAKE_ORG_ID="{creds.deeplake_org.strip()}"
"""
    # Write to the .env file in the backend folder
    with open(".env", "w") as f:
        f.write(env_content)
        
    # Update current running environment memory
    os.environ["GEMINI_API_KEY"] = creds.gemini_key.strip()
    os.environ["DEEPLAKE_API_KEY"] = creds.deeplake_key.strip()
    os.environ["DEEPLAKE_ORG_ID"] = creds.deeplake_org.strip()
    
    # Re-initialize the global database client
    global dl_client
    try:
        dl_client = Client()
    except Exception as e:
        return {"error": f"Failed to connect to DeepLake: {str(e)}"}
        
    return {"success": True}

@app.on_event("startup")
async def startup_event():
    global dl_client
    try:
        print("Connecting to DeepLake Managed Service...")
        dl_client = Client()
        print("Successfully connected to DeepLake!")
    except Exception as e:
        print(f"Failed to connect to DeepLake Workspace. Error: {e}")

@app.get("/")
def read_root():
    return {"status": "Backend is running", "active_cameras": len(active_cameras)}

@app.get("/active-cameras")
def get_active_cameras():
    # Return a list of camera objects
    cameras = [{"id": cam_id, "connected_at": data["connected_at"]} for cam_id, data in active_cameras.items()]
    return {"cameras": cameras}

@app.post("/search")
async def search_videos(query: SearchQuery):
    print(f"🔍 Searching for: '{query.text}'")
    try:
        query_vector = generate_text_embedding(query.text)
        result = dl_client.query('SELECT * FROM "ai_events"')
        
        results_with_scores = []
        for row in result:
            # Safely extract from DeepLake row object
            video_filename = row.get('video_path')
            caption_text = row.get('caption')
            row_embedding = row.get('embedding')
            event_timestamp = row.get('timestamp')
            
            if row_embedding is None:
                continue
                
            row_emb_np = np.array(row_embedding)
            dot_product = np.dot(query_vector, row_emb_np)
            norm_q = np.linalg.norm(query_vector)
            norm_r = np.linalg.norm(row_emb_np)
            similarity = dot_product / (norm_q * norm_r) if (norm_q > 0 and norm_r > 0) else 0
            
            results_with_scores.append({
                "score": float(similarity),
                "filename": str(video_filename),
                "caption": str(caption_text),
                "timestamp": str(event_timestamp) if event_timestamp else "Unknown Time"
            })

        results_with_scores.sort(key=lambda x: x["score"], reverse=True)
        top_results = results_with_scores[:query.limit]
        
        search_results = []
        for row in top_results:
            clean_filepath = row['filename'].strip("[]'\"")
            
            # Format the time nicely for the user interface
            formatted_time = row['timestamp']
            if formatted_time != "Unknown Time":
                try: 
                    # Attempt to convert '2024-03-15T14:30:00+00:00' -> 'Mar 15, 2:30 PM'
                    dt = datetime.fromisoformat(formatted_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%b %d, %I:%M %p")
                except Exception as e:
                    print(f"Error parsing date {formatted_time}: {e}")
                    pass
            
            search_results.append({
                # RETURN A RELATIVE PATH! The frontend proxy will route /api/ to the backend natively
                "video_url": f"/api/{clean_filepath}", 
                "caption": row['caption'],
                "timestamp": formatted_time
            })
            
        print(f"✅ Returning top {len(search_results)} matches.")
        return {"results": search_results}

    except Exception as e:
        print(f"❌ Search Error: {e}")
        return {"error": str(e)}
    
# --- WebSocket now takes a dynamic {camera_id} ---
@app.websocket("/ws/video/{camera_id}")
async def websocket_video_endpoint(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    active_cameras[camera_id] = { "status": "connected", "connected_at": datetime.now().isoformat() }
    try:
        data = await websocket.receive_text()
        offer_dict = json.loads(data)
        # PASS camera_id HERE
        answer_dict = await process_offer(offer_dict["sdp"], offer_dict["type"], camera_id)
        await websocket.send_text(json.dumps(answer_dict))
        while True: 
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"🚨 CRASH IN WEBSOCKET: {repr(e)}")
    finally:
        if camera_id in active_cameras: 
            del active_cameras[camera_id]

# --- NEW: Safe MJPEG Generator ---
async def generate_mjpeg_stream(camera_id: str, request: Request):
    """Yields JPEGs, but aggressively shuts down if browser disconnects."""
    while True:
        if await request.is_disconnected():
            print(f"🛑 Dashboard disconnected from {camera_id}. Dropping stream cleanly.")
            break
            
        if camera_id in latest_frames:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + latest_frames[camera_id] + b'\r\n')
            
        await asyncio.sleep(0.05) # Caps at 20 FPS to save CPU

@app.get("/live/{camera_id}")
async def get_live_stream(camera_id: str, request: Request):
    return StreamingResponse(
        generate_mjpeg_stream(camera_id, request), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )