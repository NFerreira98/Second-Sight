# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# --- Tell Next.js the proper Docker network URL during the build step! ---
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL
# ---------------------------------------------------------------------------

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]