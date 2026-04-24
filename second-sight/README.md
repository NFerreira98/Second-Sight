# Second Sight

Second Sight is an open-source, AI-powered video security and search platform. Instead of recording hours of empty footage, this system actively monitors live camera feeds, detects motion, records the event, and uses Google Gemini to write highly detailed descriptions of what happened. You can then search your entire camera history using natural language.

## Features
* **Real-Time WebRTC:** Turn any device with a web browser into a security camera node.
* **Smart Motion Detection:** Uses OpenCV to ignore background noise and only record actual events.
* **AI Comprehension:** Google Gemini 1.5 analyzes the video and audio of the event and writes a detailed caption.
* **Semantic Search:** Activeloop DeepLake vector database allows you to search for events using natural language (e.g., *"Show me the delivery driver with the red hat"*).
* **Privacy Mode:** Keep cameras online without recording.
* **1-Click Install:** Fully containerized with Docker.

---

## 📦 Installation

**Prerequisites:** You must have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed on your machine.

**1. Clone the repository**
\`\`\`bash
git clone https://github.com/YOUR_USERNAME/second-sight.git
cd second-sight
\`\`\`

**2. Start the system**
\`\`\`bash
docker-compose up --build -d
\`\`\`

**3. Initial Setup**
Open your web browser and go to:
[http://localhost:3000](http://localhost:3000)

Because this is your first time running the app, you will automatically be redirected to the **Setup Wizard**. You will need two free API keys to initialize the AI:
* A [Google AI Studio API Key](https://aistudio.google.com/app/apikey)
* An [Activeloop DeepLake API Token & Org ID](https://app.activeloop.ai/)

Once you paste your keys into the wizard, the system is permanently unlocked and ready to use!

---

## 📷 Adding Camera Nodes
To turn a laptop, tablet, or phone into a camera, open the app on that device and navigate to:
`http://<SERVER_IP>:3000/camera`

Type in a name for the camera (e.g., "Front Door") and click **Start Streaming**. The video will instantly appear on your main dashboard! *(Note: Mobile browsers require HTTPS or a localhost tunnel like Tailscale to grant camera permissions).*

---

## 🖥️ Dashboard & Features

- **Dashboard:** View all active camera feeds, search events, and manage video clips in real time.
- **Lock Clips:** Mark important video clips as "locked" to prevent auto-deletion.
- **Active Camera List:** Instantly see all connected cameras and their status.
- **No Authentication:** Anyone with access to the server can use the dashboard (no login required).

---

## 🛠️ Local Development (Optional)

You can also run the backend and frontend separately for development:

**Backend:**
```bash
cd backend
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🔒 Managing Locked Clips

- In the dashboard, you can lock video clips to prevent them from being deleted automatically.
- Locked clips are managed from the dashboard and stored in the backend.

---

## ℹ️ Notes
- Privacy Mode allows cameras to stay online without recording (see dashboard controls).
- There is no user authentication—access is open to anyone who can reach the server.
- The Setup Wizard will redirect you if API keys are missing.