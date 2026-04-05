# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from deeplake import Client
import numpy as np
import os
import json
import certifi
from dotenv import load_dotenv
from webrtc import process_offer
from gemini_client import generate_text_embedding

# Fix for Mac Python SSL Certificate errors
os.environ["SSL_CERT_FILE"] = certifi.where()

load_dotenv()

app = FastAPI(title="Second Sight API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000"], # Allow the Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. SERVE THE VIDEOS TO THE FRONTEND
# This allows the frontend to play http://localhost:8000/motion_clips/event_123.mp4
os.makedirs("motion_clips", exist_ok=True)
app.mount("/motion_clips", StaticFiles(directory="motion_clips"), name="motion_clips")

dl_client = None

# Pydantic model for the search request
class SearchQuery(BaseModel):
    text: str
    limit: int = 5

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
    return {"status": "Backend is running"}

@app.post("/search")
async def search_videos(query: SearchQuery):
    print(f"🔍 Searching for: '{query.text}'")
    
    try:
        query_vector = generate_text_embedding(query.text)
        
        # 1. Fetch all rows locally using the new SDK's table method
        # The extra () at the end executes the fetch
        rows = dl_client.table("monitoring_events")()
        
        results_with_scores = []
        row_count = 0
        
        # 2. Iterate through the rows directly
        for row in rows:
            row_count += 1
            
            # Extract data from the row dictionary
            video_filename = row.get("video")
            caption_text = row.get("caption")
            row_embedding = row.get("embedding")
            
            if row_embedding is None:
                continue
                
            # Convert to NumPy for fast math
            row_emb_np = np.array(row_embedding)
            
            # Math Cosine Similarity
            dot_product = np.dot(query_vector, row_emb_np)
            norm_q = np.linalg.norm(query_vector)
            norm_r = np.linalg.norm(row_emb_np)
            
            similarity = 0
            if norm_q > 0 and norm_r > 0:
                similarity = dot_product / (norm_q * norm_r)
            
            # Decode byte strings if necessary
            if isinstance(video_filename, bytes):
                video_filename = video_filename.decode('utf-8')
            if isinstance(caption_text, bytes):
                caption_text = caption_text.decode('utf-8')
            
            results_with_scores.append({
                "score": float(similarity),
                "filename": str(video_filename),
                "caption": str(caption_text)
            })

        print(f"📊 Downloaded and analyzed {row_count} total events.")

        # Sort the results by highest similarity score first
        results_with_scores.sort(key=lambda x: x["score"], reverse=True)
        top_results = results_with_scores[:query.limit]
        
        # Format the Output for the frontend
        search_results = []
        for row in top_results:
            # We must make sure the URL string removes any accidental array brackets if they exist
            clean_filename = row['filename'].strip("[]'\"")
            search_results.append({
                "video_url": f"http://127.0.0.1:8000/{clean_filename}",
                "caption": row['caption']
            })
            
        print(f"✅ Returning top {len(search_results)} matches to UI.")
        return {"results": search_results}

    except Exception as e:
        print(f"❌ Search Error: {e}")
        return {"error": str(e)}
    
@app.websocket("/ws/video")
async def websocket_video_endpoint(websocket: WebSocket):
    """WebSocket endpoint for WebRTC live camera streaming."""
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        offer_dict = json.loads(data)
        answer_dict = await process_offer(offer_dict["sdp"], offer_dict["type"])
        await websocket.send_text(json.dumps(answer_dict))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("WebRTC Signaling WebSocket disconnected")