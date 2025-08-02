# Kokoro Text-to-Speech Service

A FastAPI-based text-to-speech service using Kokoro TTS with multi-language support and high-quality voice synthesis.

## Features

- **Multi-Language Support**: English (US/UK), Spanish, Japanese, and Chinese
- **High-Quality Voices**: Multiple voice options per language with natural pronunciation
- **Format Conversion**: Automatic WAV to OGG conversion with Opus codec for optimal compression
- **Pipeline Caching**: Efficient language pipeline caching for better performance
- **Voice Mapping**: Smart default voice selection based on language
- **Audio Optimization**: 24kHz output with optimized bitrate for quality/size balance

## Quick Start

### Installation

```bash
pip install fastapi uvicorn numpy soundfile kokoro
# FFmpeg required for audio conversion
sudo apt-get install ffmpeg  # Ubuntu/Debian
# or
brew install ffmpeg  # macOS
```

### Run the Service

```bash
python tts_server.py
```

The service will start on `http://0.0.0.0:5007`

## API Usage

### Text-to-Speech

**Endpoint:** `POST /tts`

**Request Body:**
```json
{
  "text": "Hello, this is a test of the text-to-speech service.",
  "lang": "en"
}
```

**Parameters:**
- `text` (string): Text to convert to speech
- `lang` (string, optional): Language code - defaults to "en"
  - `en`: American English (voice: af_heart)
  - `gb`: British English (voice: bf_sunny)
  - `es`: Spanish (voice: em_alex)
  - `ja`: Japanese (voice: jf_yama)
  - `zh`: Chinese (voice: zf_xiaobei)

**Example with curl:**

```bash
curl -X POST "http://localhost:5007/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!", "lang": "en"}' \
  --output speech.ogg
```

**Response:**
Returns an OGG audio file with the synthesized speech.

### Health Check

**Endpoint:** `GET /health`

```json
{
  "status": "ok",
  "service": "tts_server"
}
```

## Voice Options

| Language | Code | Voice | Gender |
|----------|------|-------|--------|
| American English | `en` | af_heart | Female |
| British English | `gb` | bf_sunny | Female |
| Spanish | `es` | em_alex | Male |
| Japanese | `ja` | jf_yama | Female |
| Chinese | `zh` | zf_xiaobei | Female |

## Configuration

- **Audio Format**: 24kHz WAV converted to OGG with Opus codec
- **Bitrate**: 24kbps for optimal quality/size ratio
- **Temp Directory**: Audio files stored in system temp directory
- **Pipeline Caching**: Language pipelines cached for performance

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- NumPy
- SoundFile
- Kokoro TTS
- FFmpeg

## License

AGPL-3.0 (Kokoro TTS model retains its original license)
