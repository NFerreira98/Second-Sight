# backend/event_processor.py
import os
from deeplake import Client
from gemini_client import generate_video_caption, generate_text_embedding

def process_and_ingest_event(video_path: str):
    """
    Runs the AI pipeline on a saved video and pushes it to DeepLake.
    """
    try:
        print(f"--- Starting AI Pipeline for {video_path} ---")
        
        # 1. Get Caption (Video + Audio)
        caption = generate_video_caption(video_path)
        print(f"Caption: {caption}")
        
        # 2. Get Embedding
        embedding = generate_text_embedding(caption)
        
        # 3. Ingest to DeepLake
        print("Ingesting into DeepLake...")
        dl_client = Client()
        table_name = "monitoring_events"
        
        dl_client.ingest(table_name, {
            "video": [video_path],
            "caption": [caption],
            "embedding": [embedding]
        }, schema={"video": "FILE"})
        
        print("✅ Event successfully ingested!")
        
        # Optional: Delete the local .mp4 file to save hard drive space
        # os.remove(video_path)
        
    except Exception as e:
        print(f"❌ Pipeline Error: {e}")