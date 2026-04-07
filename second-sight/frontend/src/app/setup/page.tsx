// frontend/src/app/setup/page.tsx
"use client";

import Image from "next/image";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Settings, ExternalLink, Loader2 } from "lucide-react"; 

export default function SetupPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [creds, setCreds] = useState({
    gemini_key: "",
    deeplake_key: "",
    deeplake_org: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/system/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(creds),
      });

      const data = await res.json();
      
      if (data.error) throw new Error(data.error);
      
      // Success! Redirect to the dashboard
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to save configuration.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="bg-blue-600/10 border-b border-gray-800 p-8 text-center space-y-3">
          
          <div className="mx-auto w-20 h-20 mb-4 flex items-center justify-center">
            {/* The Next.js Image component looks inside the public/ folder automatically */}
            <Image 
              src="/logo.png" 
              alt="Second Sight Logo" 
              width={80} 
              height={80} 
              className="drop-shadow-[0_0_15px_rgba(59,130,246,0.5)] object-contain"
            />
          </div>
          
          <h1 className="text-3xl font-extrabold tracking-tight">System Initialization</h1>
          <p className="text-gray-400">Welcome to Second Sight. Please connect your AI and Database engines to start monitoring.</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-4 rounded-xl text-sm font-medium text-center">
              {error}
            </div>
          )}

          {/* Gemini Section */}
          <div className="space-y-3 bg-gray-950 p-5 rounded-xl border border-gray-800">
            <div className="flex justify-between items-center">
              <label className="font-semibold text-gray-200">Google Gemini API Key</label>
              <a href="https://aistudio.google.com/app/apikey" target="_blank" className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1">
                Get Key <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <input
              type="password"
              required
              value={creds.gemini_key}
              onChange={(e) => setCreds({ ...creds, gemini_key: e.target.value })}
              placeholder="AIzaSy..."
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none font-mono text-sm"
            />
          </div>

          {/* DeepLake Section */}
          <div className="space-y-3 bg-gray-950 p-5 rounded-xl border border-gray-800">
            <div className="flex justify-between items-center">
              <label className="font-semibold text-gray-200">Activeloop DeepLake Credentials</label>
              <a href="https://app.activeloop.ai" target="_blank" className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1">
                Open Dashboard <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            
            <input
              type="text"
              required
              value={creds.deeplake_org}
              onChange={(e) => setCreds({ ...creds, deeplake_org: e.target.value })}
              placeholder="Organization ID (e.g., my-username)"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none font-mono text-sm"
            />
            
            <input
              type="password"
              required
              value={creds.deeplake_key}
              onChange={(e) => setCreds({ ...creds, deeplake_key: e.target.value })}
              placeholder="DeepLake API Token (eyJhbG...)"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none font-mono text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : <><Settings className="w-5 h-5" /> Save Configuration</>}
          </button>
        </form>

      </div>
    </div>
  );
}