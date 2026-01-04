import torch
import logging

# Configure logging
logger = logging.getLogger(__name__)


def get_speech_timestamps(audio_path: str):
    """
    Detects speech segments in an audio file using Silero VAD.
    Returns a list of dicts with 'start' and 'end' keys in seconds.
    """
    try:
        # Load Silero VAD model
        # trust_repo=True is important to avoid security warnings/errors
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            trust_repo=True
        )

        (get_speech_timestamps_func, _, read_audio, _, _) = utils

        logger.info(f"Processing VAD for {audio_path}...")
        wav = read_audio(audio_path)

        # get_speech_timestamps returns a list of dicts:
        # [{'start': 0.5, 'end': 1.2}, ...]
        speech_timestamps = get_speech_timestamps_func(
            wav, model, return_seconds=True
        )

        logger.info(f"Found {len(speech_timestamps)} speech segments.")
        return speech_timestamps
    except Exception as e:
        logger.error(f"Error in VAD processing: {e}")
        raise
