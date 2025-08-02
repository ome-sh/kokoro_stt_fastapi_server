# License
#
# This software is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.
#
# Copyright (C) 2025 Roland Kohlhuber
#
# **Note:** The AI model used by this software (Kokoro TTS) retains its original license and is not subject to the AGPL license terms.
#
# For the complete license text, see: https://www.gnu.org/licenses/agpl-3.0.html

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import tempfile
import uuid
import logging
import numpy as np
import soundfile as sf
from kokoro import KPipeline
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('tts_server')

app = FastAPI()

# Temporary directory for audio files
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'tts_audio')
os.makedirs(TEMP_DIR, exist_ok=True)

# Pipeline cache for different languages
pipelines = {}

def get_pipeline(lang_code):
    """Get or create pipeline for the specified language."""
    if lang_code not in pipelines:
        logger.info(f"Initializing new pipeline for language: {lang_code}")
        pipelines[lang_code] = KPipeline(lang_code=lang_code)
    return pipelines[lang_code]

def convert_to_ogg(wav_path, ogg_path):
    """Convert WAV file to OGG with Opus codec."""
    try:
        cmd = ['ffmpeg', '-i', wav_path, '-c:a', 'libopus', '-b:a', '24k', ogg_path, '-y']
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting to OGG: {e}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        return False

class TTSRequest(BaseModel):
    text: str
    lang: str = "en"

@app.post("/tts")
def text_to_speech(request: TTSRequest):
    """Endpoint for converting text to speech."""
    try:
        text = request.text
        lang = request.lang.lower()
        
        # Map language code to Kokoro format
        lang_code_map = {
            'en': 'a',  # American English
            'gb': 'b',  # British English
            'es': 'e',  # Spanish
            'ja': 'j',  # Japanese
            'zh': 'z'   # Chinese
        }
        lang_code = lang_code_map.get(lang, 'a')
        
        # Choose default voice based on language
        voice_map = {
            'a': 'af_heart',  # American English
            'b': 'bf_sunny',  # British English
            'e': 'em_alex',  # Spanish ef_dora | em_santa | em_alex
            'j': 'jf_yama',   # Japanese
            'z': 'zf_xiaobei'     # Chinese
        }
        voice = voice_map.get(lang_code, 'af_heart')
        
        # Get TTS pipeline
        pipeline = get_pipeline(lang_code)
        
        # Generate unique ID for this request
        request_id = str(uuid.uuid4())
        wav_path = os.path.join(TEMP_DIR, f"{request_id}.wav")
        ogg_path = os.path.join(TEMP_DIR, f"{request_id}.ogg")
        
        logger.info(f"Processing TTS request: {request_id}, Language: {lang}, Text: {text[:50]}...")
        
        # Step 1: Convert text to phonemes
        generator = pipeline(text, voice=voice, speed=1, split_pattern=None)
        phonemes = None
        for gs, ps, _ in generator:
            phonemes = ps[0] if isinstance(ps, tuple) else ps  # Extract phoneme string
            break  # We only need the phonemes
        
        if not phonemes:
            raise HTTPException(status_code=500, detail="No phonemes generated from text")
        
        logger.info(f"Phonemes extracted: {phonemes[:50]}...")
        
        # Step 2: Generate audio from phonemes
        generator = pipeline.generate_from_tokens(
            tokens=phonemes,
            voice=voice,
            speed=1.0
        )
        
        # Collect all audio segments
        audio_segments = []
        for gs, ps, audio in generator:
            audio_segments.append(audio)
        
        if not audio_segments:
            raise HTTPException(status_code=500, detail="No audio segments generated from phonemes")
        
        # Combine all segments into a single audio
        combined_audio = np.concatenate(audio_segments)
        sf.write(wav_path, combined_audio, 24000)
        logger.info(f"WAV file saved: {wav_path}")
        
        # Convert WAV to OGG
        success = convert_to_ogg(wav_path, ogg_path)
        if not success:
            raise HTTPException(status_code=500, detail="Error during audio conversion")
        
        logger.info(f"Audio successfully converted to OGG: {ogg_path}")
        
        # Send OGG file to the client
        return FileResponse(
            ogg_path,
            media_type="audio/ogg",
            filename=f"speech_{request_id}.ogg"
        )
    
    except Exception as e:
        logger.error(f"Error in TTS processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
def health_check():
    """Simple endpoint for health checks."""
    return {"status": "ok", "service": "tts_server"}

if __name__ == '__main__':
    import uvicorn
    logger.info("Starting TTS server on port 5007...")
    uvicorn.run(app, host="0.0.0.0", port=5007)