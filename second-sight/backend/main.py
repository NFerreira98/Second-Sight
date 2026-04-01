from fastapi import FastAPI
import deeplake
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Second Sight API")

# Fetch credentials from .env
DEEPLAKE_ORG_ID = os.getenv("DEEPLAKE_ORG_ID")
DEEPLAKE_TOKEN = os.getenv("DEEPLAKE_TOKEN")

# Format the cloud dataset URL: hub://<org_id>/<dataset_name>
if DEEPLAKE_ORG_ID:
    DATASET_PATH = f"hub://{DEEPLAKE_ORG_ID}/second_sight"
else:
    DATASET_PATH = "./second_sight"  # Fallback to local path if org ID is not set

def init_db():
    """
    Initializes the DeepLake dataset securely in the cloud.
    """
    # Check if the dataset exists in the cloud
    if not deeplake.exists(DATASET_PATH, token=DEEPLAKE_TOKEN):
        # Create an empty DeepLake dataset in the cloud
        ds = deeplake.empty(DATASET_PATH, token=DEEPLAKE_TOKEN)
        
        with ds:
            ds.create_tensor('id', htype='text')
            ds.create_tensor('frames', htype='image', sample_compression='jpeg')
            ds.create_tensor('caption', htype='text')
            ds.create_tensor('embedding', htype='generic')
            
        print(f"DeepLake dataset initialized at {DATASET_PATH}.")
    else:
        print(f"DeepLake dataset already exists at {DATASET_PATH}.")

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"status": "Backend is running"}