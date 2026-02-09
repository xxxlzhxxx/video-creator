# Video Creator

AI-powered video generation and editing platform using **Doubao-Seedance-2.0** model via Volcengine Ark API.

## Features

| Mode | Input | Description |
|------|-------|-------------|
| Text-to-Video | Text prompt | Generate video from text description |
| Image-to-Video | Image + Text | Animate static images with motion prompts |
| Video Editing | Video/Image + Instructions | Modify or extend existing videos |

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
ARK_API_KEY=your-api-key-here
VIDEO_ENDPOINT=ep-xxxxxx  # Doubao-Seedance-2.0 endpoint
LLM_ENDPOINT=ep-xxxxxx    # LLM endpoint for prompt enhancement (optional)
```

### 3. Start Server

```bash
python web_server.py
```

The server will start at http://localhost:5001

## Project Structure

```
videoCreater/
├── config.py           # Configuration management
├── video_generator.py  # Core video generation module
├── llm_client.py       # LLM prompt enhancement
├── web_server.py       # Flask API server
├── static/
│   └── index.html      # Web UI
├── requirements.txt
└── .env.example        # Environment template
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/upload` | POST | Upload image/video file |
| `/api/generate` | POST | Start generation task |
| `/api/status/<task_id>` | GET | Get task status |
| `/api/download/<task_id>` | GET | Download video |
| `/api/preview/<task_id>` | GET | Preview video |

## Usage

### Web Interface

1. Open http://localhost:5001
2. Select mode (Text-to-Video / Image-to-Video / Edit)
3. Enter prompt or upload file
4. Click "Start Generation"
5. Wait for completion, then preview/download

### Python API

```python
from video_generator import VideoGenerator

gen = VideoGenerator()

# Text-to-Video
result = gen.generate_from_text(
    "A sunset over the ocean with waves gently crashing on the beach",
    ratio="16:9",
    duration=5
)
print(result)

# Image-to-Video
result = gen.generate_from_image(
    "path/to/image.jpg",
    motion_prompt="Camera slowly zooms in, petals falling",
    ratio="16:9",
    duration=8
)
```

## Configuration Options

- **Aspect Ratio**: 16:9, 9:16, 1:1, 4:3, 21:9
- **Duration**: 5-12 seconds
- **Image Formats**: PNG, JPG, GIF, WebP
- **Video Formats**: MP4, WebM, MOV

## Notes

- Video generation typically takes 1-3 minutes
- API key requires access to Doubao-Seedance-2.0 model
- Generated videos are saved in `output/videos/`

## License

MIT
