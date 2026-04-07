/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Use the Docker URL if it exists, otherwise default to local Mac development
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`, 
      },
    ];
  },
};

export default nextConfig;