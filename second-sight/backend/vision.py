# backend/vision.py
import cv2
import numpy as np
import asyncio
import time

motion_state = {"is_active": False}
latest_frames = {} # Stores JPEG frames for the dashboard

PROCESSING_WIDTH = 640
PROCESSING_HEIGHT = 480
MOTION_COOLDOWN_SECONDS = 5

# --- Accepts camera_id again ---
async def process_video_track(track, camera_id: str):
    print(f"Started OpenCV processing for {camera_id}...")
    
    back_sub = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=50, detectShadows=False)
    last_motion_time = 0
    was_paused = False 

    try:
        while True:
            frame = await track.recv()
            img = frame.to_ndarray(format="bgr24")
            img = cv2.resize(img, (PROCESSING_WIDTH, PROCESSING_HEIGHT))

            # --- 1. Update the Dashboard MJPEG ---
            _, buffer = cv2.imencode('.jpg', img)
            latest_frames[camera_id] = buffer.tobytes()

            # --- 2. Motion & Privacy Detection ---
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            if np.mean(gray) < 1.0:
                # Privacy Mode (Black Screen)
                was_paused = True
                motion_detected = False
            else:
                if was_paused:
                    # Just unpaused, ignore the sudden light jump
                    back_sub = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=50, detectShadows=False)
                    was_paused = False
                    motion_detected = False
                else:
                    # Normal Motion Detection
                    gray = cv2.GaussianBlur(gray, (21, 21), 0)
                    fg_mask = back_sub.apply(gray, learningRate=-1)
                    thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)[1]
                    thresh = cv2.dilate(thresh, None, iterations=2)

                    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    motion_detected = any(cv2.contourArea(c) > 2000 for c in contours)

            current_time = time.time()

            if motion_detected:
                last_motion_time = current_time
                if not motion_state["is_active"]:
                    print(f"🚨 Motion Detected on {camera_id}! Triggering recording...")
                    motion_state["is_active"] = True
            else:
                if motion_state["is_active"] and (current_time - last_motion_time > MOTION_COOLDOWN_SECONDS):
                    print(f"✅ Motion stopped. Stopping recording...")
                    motion_state["is_active"] = False

    except Exception as e:
        print(f"Video track processing stopped: {e}")
        motion_state["is_active"] = False
        if camera_id in latest_frames:
            del latest_frames[camera_id]