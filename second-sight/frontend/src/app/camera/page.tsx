// src/app/camera/page.tsx
"use client";

import { useEffect, useRef, useState } from "react";

export default function CameraPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState("Initializing...");

  useEffect(() => {
    let pc: RTCPeerConnection | null = null;
    let ws: WebSocket | null = null;
    let localStream: MediaStream | null = null;
    let reconnectTimer: NodeJS.Timeout;

    // 1. Get the camera once so we don't spam the user with permission popups
    async function initCamera() {
      try {
        setStatus("Requesting camera access...");
        localStream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720 },
          audio: true,
        });

        if (videoRef.current) {
          videoRef.current.srcObject = localStream;
        }
        
        // Once we have the camera, start the connection loop
        connectToBackend();
      } catch (err) {
        console.error(err);
        setStatus("Error accessing camera");
      }
    }

    // 2. The connection logic that can be repeated if it fails
    function connectToBackend() {
      if (!localStream) return;

      // Clean up old connections if we are reconnecting
      if (pc) pc.close();
      if (ws) ws.close();

      setStatus("Connecting to backend...");
      pc = new RTCPeerConnection();

      // Add camera tracks to the new peer connection
      localStream.getTracks().forEach((track) => {
        pc!.addTrack(track, localStream!);
      });

      ws = new WebSocket("ws://127.0.0.1:8000/ws/video");

      ws.onopen = async () => {
        setStatus("Negotiating connection...");
        const offer = await pc!.createOffer();
        await pc!.setLocalDescription(offer);
        
        ws!.send(JSON.stringify({ sdp: offer.sdp, type: offer.type }));
      };

      ws.onmessage = async (event) => {
        const answer = JSON.parse(event.data);
        await pc!.setRemoteDescription(new RTCSessionDescription(answer));
        setStatus("Connected & Streaming to AI 🟢");
      };

      ws.onerror = () => {
        // We let onclose handle the reconnect logic
        console.error("WebSocket Error");
      };

      // 3. Auto-Reconnect Logic
      ws.onclose = () => {
        setStatus("Disconnected. Retrying in 3 seconds... 🟠");
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(() => {
          connectToBackend();
        }, 3000);
      };
    }

    initCamera();

    // Cleanup when leaving the page entirely
    return () => {
      clearTimeout(reconnectTimer);
      if (pc) pc.close();
      if (ws) ws.close();
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-3xl w-full flex flex-col gap-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">Live Camera Node</h1>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            status.includes("Streaming") ? "bg-green-500/20 text-green-400" : 
            status.includes("Retrying") ? "bg-orange-500/20 text-orange-400" :
            "bg-yellow-500/20 text-yellow-400"
          }`}>
            {status}
          </span>
        </div>
        
        <div className="relative aspect-video bg-black rounded-xl overflow-hidden border border-gray-800 shadow-lg">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover transform scale-x-[-1]" 
          />
        </div>
      </div>
    </div>
  );
}