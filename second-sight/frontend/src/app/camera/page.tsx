// frontend/src/app/camera/page.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { Video, VideoOff } from "lucide-react";

export default function CameraPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // New States for the Setup Screen
  const [cameraId, setCameraId] = useState("");
  const [isStarted, setIsStarted] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [status, setStatus] = useState("Waiting to start...");

  useEffect(() => {
    // Don't run the connection logic until the user enters a name and clicks Start
    if (!isStarted || !cameraId) return;

    let pc: RTCPeerConnection | null = null;
    let ws: WebSocket | null = null;
    let localStream: MediaStream | null = null;
    let reconnectTimer: NodeJS.Timeout;

    async function initCamera() {
      try {
        setStatus("Requesting camera access...");
        localStream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720 },
          audio: true, // Audio enabled!
        });

        streamRef.current = localStream; 

        if (videoRef.current) {
          videoRef.current.srcObject = localStream;
        }
        
        connectToBackend();
      } catch (err) {
        console.error(err);
        setStatus("Error accessing camera. Please allow permissions.");
      }
    }

    function connectToBackend() {
      if (!localStream) return;

      if (pc) pc.close();
      if (ws) ws.close();

      setStatus("Connecting to backend...");
      pc = new RTCPeerConnection();

      localStream.getTracks().forEach((track) => {
        pc!.addTrack(track, localStream!);
      });

      // Format the name securely (replace spaces with underscores)
      const safeId = encodeURIComponent(cameraId.trim().replace(/\s+/g, "_"));
      
      // Connect using the custom dynamic ID
      ws = new WebSocket(`ws://localhost:8000/ws/video/${safeId}`);

      ws.onopen = async () => {
        setStatus("Negotiating connection...");
        const offer = await pc!.createOffer();
        await pc!.setLocalDescription(offer);
        ws!.send(JSON.stringify({ sdp: offer.sdp, type: offer.type }));
      };

      ws.onmessage = async (event) => {
        const answer = JSON.parse(event.data);
        await pc!.setRemoteDescription(new RTCSessionDescription(answer));
        setStatus("Connected & Streaming 🟢");
      };

      ws.onclose = () => {
        setStatus("Disconnected. Retrying in 3 seconds... 🟠");
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(() => connectToBackend(), 3000);
      };
    }

    initCamera();

    return () => {
      clearTimeout(reconnectTimer);
      if (pc) pc.close();
      if (ws) ws.close();
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [isStarted, cameraId]);


  const handleTogglePause = () => {
    const newState = !isPaused;
    setIsPaused(newState);
    
    if (streamRef.current) {
      // Toggling track.enabled sends black frames/silence to the backend automatically
      streamRef.current.getTracks().forEach(track => {
        track.enabled = !newState;
      });
    }
  };

  const handleStopStreaming = () => {
    setIsStarted(false);
    setStatus("Waiting to start...");
    // The useEffect cleanup return() will automatically handle closing the WebSockets and PC's!
  };

  // --- 1. SETUP SCREEN ---
  if (!isStarted) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white p-8">
        <div className="max-w-md w-full bg-gray-900 border border-gray-800 p-8 rounded-2xl shadow-2xl flex flex-col gap-6 items-center">
          <div className="bg-blue-500/20 p-4 rounded-full">
            <Video className="w-8 h-8 text-blue-400" />
          </div>
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold">New Camera Node</h1>
            <p className="text-gray-400 text-sm">Deploy this device as a security camera.</p>
          </div>
          
          <div className="w-full flex flex-col gap-2 mt-2">
            <input
              type="text"
              value={cameraId}
              onChange={(e) => setCameraId(e.target.value)}
              placeholder="e.g., Front Door, Warehouse"
              className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-center"
              autoFocus
              onKeyDown={(e) => { if (e.key === 'Enter' && cameraId.trim()) setIsStarted(true); }}
            />
          </div>
          
          <button
            onClick={() => setIsStarted(true)}
            disabled={!cameraId.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-800 disabled:text-gray-500 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            Start Streaming
          </button>
        </div>
      </div>
    );
  }

  // --- 2. LIVE CAMERA SCREEN ---
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-3xl w-full flex flex-col gap-4">
        
        <div className="flex justify-between items-center bg-gray-900 p-4 rounded-xl border border-gray-800">
          <div className="flex items-center gap-3">
            <Video className="w-5 h-5 text-gray-400" />
            <h1 className="text-xl font-bold">{cameraId}</h1>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            isPaused ? "bg-yellow-500/20 text-yellow-400" :
            status.includes("Streaming") ? "bg-green-500/20 text-green-400" : 
            status.includes("Retrying") ? "bg-orange-500/20 text-orange-400" :
            "bg-yellow-500/20 text-yellow-400"
          }`}>
            {isPaused ? "Paused (Privacy Mode)" : status}
          </span>
        </div>
        
        <div className="relative aspect-video bg-black rounded-xl overflow-hidden border border-gray-800 shadow-xl">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`w-full h-full object-cover transform scale-x-[-1] transition-opacity ${isPaused ? 'opacity-10' : 'opacity-100'}`} 
          />
          
          {/* OFFLINE / PAUSED OVERLAY */}
          {isPaused && (
           <div className="absolute inset-0 flex flex-col items-center justify-center backdrop-blur-md">
             <VideoOff className="w-12 h-12 text-gray-400 mb-2" />
             <p className="text-gray-400 font-medium tracking-widest text-sm uppercase">Privacy Mode Active</p>
           </div>
          )}
        </div>

        {/* CONTROLS */}
        <div className="flex gap-2 mt-2">
          {/* Pause Button */}
          <button 
            onClick={handleTogglePause}
            className={`flex-1 font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2 ${
              isPaused ? "bg-green-600 hover:bg-green-700 text-white" : "bg-yellow-600 hover:bg-yellow-700 text-white"
            }`}
          >
            {isPaused ? <Video className="w-5 h-5" /> : <VideoOff className="w-5 h-5" />}
            {isPaused ? "Resume Feed" : "Pause Feed"}
          </button>

          {/* Hard Stop Button */}
          <button 
            onClick={handleStopStreaming}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            Disconnect Node
          </button>
        </div>

      </div>
    </div>
  );
}