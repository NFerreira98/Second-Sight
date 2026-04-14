# backend/gemini_client.py
import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client():
    """Lazy-loads the client only when needed."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing. Please complete the Setup Wizard.")
    return genai.Client(api_key=api_key)

def generate_video_caption(video_path: str) -> str:
    """Uploads the .mp4 file to Gemini and asks it to describe the video."""
    client = get_gemini_client()
    print(f"Uploading {video_path} to Gemini...")
    
    video_file = client.files.upload(file=video_path)
    
    while video_file.state.name == "PROCESSING":
        print("Gemini is processing the video...")
        time.sleep(2)
        video_file = client.files.get(name=video_file.name)
        
        if video_file.state.name == "FAILED":
            # Ask Google for the exact error message
            error_details = getattr(video_file, "error", "No specific error provided by Google")
            
            # We still want to delete the broken file from their servers
            client.files.delete(name=video_file.name)
            
            # Throw the exception with the real error!
            raise Exception(f"Google Gemini failed to process this video file. Reason: {error_details}")
            
    prompt = """
    Analyze this video in detail and describe the main action or 
    event, the setting and environment, any notable movements or 
    changes, and key details about the subjects involved. 
    Listen to the audio and include any important sounds.
    Please provide a natural, flowing description.
    """
    
    print("Generating caption...")
    response = client.models.generate_content(
        model='gemini-flash-latest', 
        contents=[prompt, video_file]
    )
    
    client.files.delete(name=video_file.name)
    return response.text.strip()

def generate_text_embedding(text: str) -> list[float]:
    """Converts the text caption into a 768-D mathematical vector."""
    client = get_gemini_client()
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return response.embeddings[0].values