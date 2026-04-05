# backend/gemini_client.py
import os
from google import genai
from dotenv import load_dotenv
import time

load_dotenv()

# Initialize the new Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_video_caption(video_path: str) -> str:
    """
    Uploads the .mp4 file to Gemini, waits for it to process, 
    and asks it to describe the video and audio.
    """
    print(f"Uploading {video_path} to Gemini...")
    video_file = client.files.upload(file=video_path)
    
    # Gemini needs a few seconds to process video/audio files before it can analyze them
    while video_file.state.name == "PROCESSING":
        print("Gemini is processing the video...")
        time.sleep(2)
        video_file = client.files.get(name=video_file.name)
        
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
    
    # Cleanup file from Google's servers
    client.files.delete(name=video_file.name)
        
    return response.text.strip()


def generate_text_embedding(text: str) -> list[float]:
    """
    Converts the text caption into a 768-dimensional mathematical vector
    so we can perform semantic search later.
    """
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    # The new SDK returns the values slightly differently
    return response.embeddings[0].values
