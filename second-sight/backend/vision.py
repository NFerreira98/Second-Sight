# backend/vision.py
import cv2
import numpy as np
import asyncio
import os

os.makedirs("motion_clips", exist_ok=True)

PROCESSING_WIDTH = 640
PROCESSING_HEIGHT = 480

async def process_video_track(track):
    print("Started OpenCV MOG2 video processing task...")
    
    # Use OpenCV's built-in intelligent background subtractor
    # history=500 frames, varThreshold=50 (higher = less sensitive)
    back_sub = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=50, detectShadows=False)
    
    motion_counter = 0

    try:
        while True:
            frame = await track.recv()
            img = frame.to_ndarray(format="bgr24")
            img = cv2.resize(img, (PROCESSING_WIDTH, PROCESSING_HEIGHT))
            
            # Apply grayscale and blur to reduce camera noise
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # Let MOG2 calculate the foreground mask automatically
            # Learning rate is set to -1 so it auto-adapts continuously
            fg_mask = back_sub.apply(gray, learningRate=-1)
            
            # Clean up the mask
            thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)

            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            motion_detected = False
            for contour in contours:
                # Ignore small movements (like shadows or noise)
                if cv2.contourArea(contour) < 2000:
                    continue
                motion_detected = True
                break

            if motion_detected:
                motion_counter += 1
                if motion_counter % 30 == 0: 
                    print(f"🚨 Motion Detected! Capture event {motion_counter}")
                    cv2.imwrite(f"motion_clips/motion_{motion_counter}.jpg", img)
            else:
                # Reset counter quickly if motion stops
                motion_counter = 0

    except Exception as e:
        print(f"Video track processing stopped: {e}")