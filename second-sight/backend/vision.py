# backend/vision.py
import cv2
import numpy as np
import asyncio
import time

# Shared state read by webrtc.py to trigger the audio/video recorder
motion_state = {"is_active": False}

PROCESSING_WIDTH = 640
PROCESSING_HEIGHT = 480
MOTION_COOLDOWN_SECONDS = 5  # Keep recording for 5 seconds after motion stops

async def process_video_track(track):
    print("Started OpenCV MOG2 video processing task...")
    
    back_sub = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=50, detectShadows=False)
    last_motion_time = 0

    try:
        while True:
            # Receive the frame from WebRTC
            frame = await track.recv()
            img = frame.to_ndarray(format="bgr24")
            img = cv2.resize(img, (PROCESSING_WIDTH, PROCESSING_HEIGHT))
            
            # Apply grayscale and blur to reduce noise
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # Apply background subtraction
            fg_mask = back_sub.apply(gray, learningRate=-1)
            
            # Clean up the mask
            thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)

            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            motion_detected = False
            for contour in contours:
                if cv2.contourArea(contour) > 2000:
                    motion_detected = True
                    break

            current_time = time.time()

            if motion_detected:
                last_motion_time = current_time
                if not motion_state["is_active"]:
                    print("🚨 Motion Detected! Triggering recording...")
                    motion_state["is_active"] = True
            else:
                # If no motion for X seconds, turn off the recording state
                if motion_state["is_active"] and (current_time - last_motion_time > MOTION_COOLDOWN_SECONDS):
                    print(f"✅ Motion stopped for {MOTION_COOLDOWN_SECONDS} seconds. Stopping recording...")
                    motion_state["is_active"] = False

    except Exception as e:
        print(f"Video track processing stopped: {e}")
        motion_state["is_active"] = False