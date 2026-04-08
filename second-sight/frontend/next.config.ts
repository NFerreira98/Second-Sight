/** @type {import('next').NextConfig} */
const nextConfig = {
  
  allowedDevOrigins: ['10.0.0.189'],

  async rewrites() {
    // If not in Docker (BACKEND_URL undefined), force IPv4 local routing
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