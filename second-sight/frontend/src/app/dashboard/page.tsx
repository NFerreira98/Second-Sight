// frontend/src/app/dashboard/page.tsx
"use client";

import { useState } from "react";
import { Search, Loader2, PlaySquare } from "lucide-react";

interface SearchResult {
  video_url: string;
  caption: string;
}

export default function DashboardPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setResults([]);

    try {
      const res = await fetch("http://127.0.0.1:8000/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: query, limit: 6 }), // Request top 6 results
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

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header Setup */}
        <div className="text-center space-y-2 pt-12 pb-6">
          <h1 className="text-4xl font-extrabold tracking-tight">Second Sight</h1>
          <p className="text-gray-400">Search your camera history using natural language.</p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="max-w-2xl mx-auto relative">
          <div className="relative flex items-center">
            <Search className="absolute left-4 text-gray-500 w-5 h-5" />
            <input
              type="text"
              placeholder="e.g., Show me the delivery driver dropping off a package..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-gray-900 border border-gray-800 rounded-full py-4 pl-12 pr-32 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 shadow-lg"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="absolute right-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-full font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Search"}
            </button>
          </div>
        </form>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg text-center max-w-2xl mx-auto">
            {error}
          </div>
        )}

        {/* Video Results Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-8">
          {results.map((result, index) => (
            <div key={index} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-lg flex flex-col group transition-all hover:ring-2 hover:ring-blue-500/30">
              {/* Video Player */}
              <div className="relative aspect-video bg-black flex items-center justify-center">
                <video 
                  src={result.video_url} 
                  controls 
                  className="w-full h-full object-contain"
                  poster="" // You could potentially send a thumbnail URL from backend here later
                />
              </div>
              
              {/* AI Details */}
              <div className="p-5 flex-1 flex flex-col gap-3">
                <div className="flex items-start gap-2">
                  <PlaySquare className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {result.caption}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {!loading && results.length === 0 && !error && query && (
          <div className="text-center text-gray-500 py-12">
            No matches found for your search.
          </div>
        )}

      </div>
    </div>
  );
}