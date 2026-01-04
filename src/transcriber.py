import whisper
import logging
import torch
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def transcribe_video(
    video_path: str,
    output_language: str = "en",
    use_vad: bool = True,
    model_size: str = "base"
) -> List[Dict[str, Any]]:

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading Whisper model '{model_size}' on {device}...")
    model = whisper.load_model(model_size, device=device)

    # Determine task and language arguments for Whisper
    # Whisper 'translate' task is always to English.
    # 'transcribe' task preserves source language.
    if output_language.lower() == "en":
        task = "translate"
        whisper_lang = None  # Let Whisper detect source language
    else:
        task = "transcribe"
        whisper_lang = output_language  # Assume source is the output language
        logger.warning(
            f"Output language set to '{output_language}'. "
            "Whisper only supports translation TO English. "
            f"Assuming source language is '{output_language}' "
            "and using 'transcribe' task."
        )

    if use_vad:
        from .vad import get_speech_timestamps
        logger.info("Detecting speech segments using Silero VAD...")
        timestamps = get_speech_timestamps(video_path)

        logger.info("Loading audio for transcription...")
        audio = whisper.load_audio(video_path)

        subtitles = []

        logger.info(f"Transcribing {len(timestamps)} segments...")
        for segment in timestamps:
            start_sec = segment['start']
            end_sec = segment['end']

            start_sample = int(start_sec * 16000)
            end_sample = int(end_sec * 16000)

            audio_segment = audio[start_sample:end_sample]

            # Skip very short segments (< 0.1s)
            if len(audio_segment) < 1600:
                continue

            # Transcribe segment
            result = model.transcribe(
                audio_segment,
                language=whisper_lang,
                task=task,
                fp16=False if device == "cpu" else True
            )

            text = result['text'].strip()
            if text:
                subtitles.append({
                    'start': start_sec,
                    'end': end_sec,
                    'text': text
                })

        return subtitles
    else:
        logger.info(f"Transcribing full video with Whisper (task={task})...")
        result = model.transcribe(
            video_path,
            task=task,
            language=whisper_lang,
            fp16=False if device == "cpu" else True
        )
        return result['segments']
