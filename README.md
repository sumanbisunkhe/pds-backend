# AI-Powered Photo Distribution System - Backend

The core processing engine for the AI-powered Photo Distribution System. This backend handles face recognition, image processing, cloud storage integration, and automated delivery via Telegram.

## 🧠 Features

- **Face Recognition**: Advanced face detection and encoding using the `face_recognition` library (128D encodings).
- **Automated Processing**:
  - FTP Server for direct uploads from professional cameras.
  - Local file monitoring (Watchdog) for instant processing.
  - Cloudinary integration for scalable photo storage.
- **Instant Delivery**: Telegram Bot for user registration and automated matching notifications.
- **Real-time Updates**: Server-Sent Events (SSE) for pushing updates to the frontend.
- **Data Persistence**: MongoDB Atlas for storing user face encodings and photo metadata.
- **Resilient**: Automatic image optimization and error handling for free-tier environments.

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.9+)
- **AI/ML**: `face_recognition`, `dlib`, `numpy`
- **Database**: [MongoDB Atlas](https://www.mongodb.com/atlas)
- **Storage**: [Cloudinary](https://cloudinary.com/)
- **Messaging**: [Telegram Bot API](https://core.telegram.org/bots)
- **Networking**: `pyftpdlib` (FTP), `httpx`

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- [CMake](https://cmake.org/download/) (required for `dlib` compilation)
- C++ Build Tools (Visual Studio or GCC)

### Installation

1. Navigate to the backend directory:

   ```bash
   cd pds-backend
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/macOS
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```env
# Cloudinary
CLOUDINARY_CLOUD_NAME=your_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret

# MongoDB
MONGODB_URI=your_mongodb_connection_string

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# API
VITE_API_URL=http://localhost:5173
```

### Running the Services

The system consists of two main components:

1. **API Server**:

   ```bash
   python -m app.main
   ```

2. **FTP Receiver / File Watcher**:
   ```bash
   python scripts/ftp_receiver.py
   ```

## 🏗️ Architecture

- `app/api`: FastAPI routes and endpoint logic.
- `app/services`: Core logic (Face recognition, Cloudinary, Telegram, DB).
- `app/models`: Pydantic models for data validation.
- `scripts/`: Monitoring and secondary services like the FTP receiver.

## 📄 License

This project is part of the Photo Distribution System.
