// frontend/src/app/dashboard/page.tsx
"use client";

import { useEffect, useState } from "react";
import { Search, Loader2, PlaySquare, X, Video } from "lucide-react";

interface SearchResult {
  video_url: string;
  caption: string;
  timestamp?: string;
}

interface CameraNode {
  id: string;
  connected_at: string;
}

export default function DashboardPage() {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(5);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false); 
  
  const [activeCameras, setActiveCameras] = useState<CameraNode[]>([]);

  // Fetch Active Cameras List every 3 seconds
  useEffect(() => {
    let isMounted = true;

    async function fetchCameras() {
      try {
        const res = await fetch("/api/active-cameras");
        if (res.ok && isMounted) {
          const data = await res.json();
          const sorted = data.cameras.sort((a: CameraNode, b: CameraNode) => a.id.localeCompare(b.id));
          setActiveCameras(sorted);
        }
      } catch (err) {
        console.error("Failed to fetch active cameras:", err);
      }
    }

    fetchCameras();
    const interval = setInterval(fetchCameras, 3000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setResults([]);
    setHasSearched(true); // Switch view to Search Results

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: query, limit }),
      });

      if (!res.ok) throw new Error("Search request failed");

      const data = await res.json();
      if (data.error) throw new Error(data.error);

      setResults(data.results || []);
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setQuery("");
    setResults([]);
    setHasSearched(false); // Switch view back to Live Cameras
    setError("");
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* === HEADER & SEARCH BAR === */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 pt-6 pb-6">
          <div className="text-center md:text-left shrink-0">
            <h1 className="text-3xl font-extrabold tracking-tight">Second Sight</h1>
            <p className="text-gray-400 text-sm mt-1">AI Video Monitoring & Search</p>
          </div>

          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-3 w-full max-w-2xl">
            <div className="relative flex-1 flex items-center">
              <Search className="absolute left-4 text-gray-500 w-5 h-5" />
              <input
                type="text"
                placeholder="Search history (e.g., 'delivery driver')..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full bg-gray-900 border border-gray-800 rounded-xl py-3 pl-12 pr-12 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                disabled={loading}
              />
              {hasSearched && !loading && (
                <button type="button" onClick={clearSearch} className="absolute right-4 text-gray-400 hover:text-white transition-colors">
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            <div className="shrink-0 flex gap-2">
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                disabled={loading}
                className="w-28 bg-gray-900 border border-gray-800 rounded-xl px-3 py-3 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none text-sm cursor-pointer"
              >
                <option value={1}>1 Result</option>
                <option value={3}>3 Results</option>
                <option value={5}>Top 5</option>
                <option value={10}>Top 10</option>
              </select>
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-3 rounded-xl font-medium transition-colors disabled:opacity-50 flex items-center justify-center min-w-[100px]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Search"}
              </button>
            </div>
          </form>
        </div>

        <hr className="border-gray-800" />

        {/* === VIEW STATE ROUTING === */}
        {!hasSearched ? (
          
          /* --- 1. LIVE CAMERAS STATE --- */
          <div className="space-y-6 min-h-[400px]">
            <div className="flex items-center justify-between pb-2 border-b border-gray-800">
              <div className="flex items-center gap-3 text-gray-300">
                <span className="relative flex h-3 w-3">
                  {activeCameras.length > 0 && (
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  )}
                  <span className={`relative inline-flex rounded-full h-3 w-3 ${activeCameras.length > 0 ? "bg-green-500" : "bg-red-500"}`}></span>
                </span>
                <h2 className="text-xl font-semibold">Active Camera Nodes ({activeCameras.length})</h2>
              </div>
            </div>
            
            {activeCameras.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-gray-500 bg-gray-900/50 border border-gray-800 border-dashed rounded-2xl">
                <Video className="w-12 h-12 mb-3 opacity-30" />
                <p className="text-lg font-medium">No active cameras found on the network.</p>
                <p className="text-sm mt-1">Open <code>/camera</code> in a new tab to start a node.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {activeCameras.map((cam) => (
                  <div key={cam.id} className="relative aspect-video bg-gray-900 border border-gray-700 hover:border-blue-500/50 rounded-xl shadow-[0_0_15px_rgba(59,130,246,0.05)] flex flex-col items-center justify-center text-gray-400 overflow-hidden group transition-colors">
                    <Video className="w-12 h-12 mb-3 opacity-60 text-blue-500 group-hover:scale-110 transition-transform duration-300" />
                    <p className="text-lg font-bold text-gray-200">{cam.id.replace(/_/g, ' ')}</p>
                    <p className="text-xs mt-1 opacity-70">
                      Connected: {new Date(cam.connected_at).toLocaleTimeString()}
                    </p>
                    <div className="absolute top-3 right-3 flex items-center justify-center p-1.5 bg-green-500/20 rounded-full animate-pulse">
                        <div className="w-2 h-2 bg-green-500 rounded-full shadow-[0_0_10px_rgba(34,197,94,1)]"></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        ) : (

          /* --- 2. SEARCH RESULTS STATE --- */
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-300 flex items-center gap-2">
                <Search className="w-5 h-5 text-blue-500" />
                Search Results
              </h2>
              <p className="text-sm text-gray-500">Found {results.length} matches</p>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg text-center font-medium">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {results.map((result, index) => (
                <div key={index} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-lg flex flex-col group hover:ring-2 hover:ring-blue-500/30 transition-all">
                  <div className="relative aspect-video bg-black flex items-center justify-center border-b border-gray-800">
                    <video src={result.video_url} controls className="w-full h-full object-contain" />
                  </div>
                  <div className="p-5 flex-1 flex flex-col gap-3">
                    {result.timestamp && (
                      <p className="text-xs text-blue-400 font-mono tracking-wide uppercase">
                        {result.timestamp}
                      </p>
                    )}
                    <div className="flex items-start gap-2">
                      <PlaySquare className="w-5 h-5 text-gray-500 shrink-0 mt-0.5" />
                      <p className="text-gray-300 text-sm leading-relaxed" title={result.caption}>
                        {result.caption}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {!loading && results.length === 0 && !error && (
              <div className="text-center bg-gray-900 border border-gray-800 rounded-xl py-12 text-gray-500">
                No exact matches found. Try rewording your search!
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}