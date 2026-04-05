# backend/event_processor.py
import os
from datetime import datetime, timezone
from deeplake import Client
from gemini_client import generate_video_caption, generate_text_embedding

def process_and_ingest_event(video_path: str):
    """
    Runs the AI pipeline on a saved video and pushes it to DeepLake.
    """
    try:
        print(f"--- Starting AI Pipeline for {video_path} ---")
        
        # 1. Grab current time in standard ISO format
        event_time = datetime.now(timezone.utc).isoformat()
        
        # 2. Get Caption (Video + Audio)
        caption = generate_video_caption(video_path)
        print(f"Caption: {caption}")
        
        # 3. Get Embedding
        embedding = generate_text_embedding(caption)
        
        # 4. Ingest to DeepLake (No schema parsing, pure data)
        print("Ingesting into DeepLake...")
        dl_client = Client()
        table_name = "ai_events"
        
        dl_client.ingest(table_name, {
            "video_path": [video_path],
            "caption": [caption],
            "embedding": [embedding],
            "timestamp": [event_time] # <--- Added the new timestamp column
        })
        
        print(f"✅ Event from {event_time} successfully ingested!")
        
    except Exception as e:
        print(f"❌ Pipeline Error: {e}")