# Meeting Analyzer Backend

This is the backend for the Meeting Analyzer app. It provides APIs for:
- Managing meetings (with Jitsi/WebRTC integration)
- Real-time audio transcription using Whisper
- Generating meeting insights using OpenAI LLM

## Features

- FastAPI + SQLModel + PostgreSQL
- Real-time audio transcription via WebSocket
- Whisper (open source) for speech-to-text
- OpenAI GPT for meeting insights
- Dockerized for easy deployment

## Project Structure

```
backend/
  app/
    config.py
    main.py
    models/
    routers/
    services/
    utils/
  requirements.txt
  Dockerfile
docker-compose.yml
.env.example
```

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd meeting-analyzer/backend
```

### 2. Set up environment variables

Copy `.env.example` to `.env` and fill in your OpenAI API key and secret key.

### 3. Build and run with Docker Compose

```bash
docker-compose up --build
```

- The backend will be available at `http://localhost:8000`
- PostgreSQL will be available at `localhost:5432`

### 4. API Documentation

Visit `http://localhost:8000/docs` for the interactive FastAPI docs.

## Notes

- Make sure your machine supports running Whisper (requires ffmpeg and torch).
- The backend expects audio chunks over WebSocket at `/ws/audio/{meeting_id}`.
- Insights are generated at the end of the meeting using OpenAI GPT.

## License

MIT 