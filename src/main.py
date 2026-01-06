import typer
import logging
from pathlib import Path
from typing import Optional
from .utils import write_srt

app = typer.Typer(
    help="CLI tool to generate SRT subtitles using Whisper and Silero VAD."
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.command()
def generate(
    input_path: Path = typer.Argument(
        ...,
        help="Path to video file or directory of videos.",
        exists=True
    ),
    output_language: str = typer.Option(
        "en",
        help="Target language (e.g., 'en'). Whisper translates TO English."
    ),
    model_size: str = typer.Option(
        "base",
        help="Whisper model size (tiny, base, small, medium, large)."
    ),
    use_vad: bool = typer.Option(
        True,
        help="Use Silero VAD for speech detection."
    ),
    high_quality: bool = typer.Option(
        False,
        "--high-quality", "-hq",
        help="Enable beam search and strict decoding for better quality (slower)."
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        help="Directory to save SRT files. Defaults to input directory."
    )
):
    """
    Generate SRT subtitles for video file(s).
    """
    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        # Extensions to look for
        extensions = {
            ".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".flac", ".m4a"
        }
        files = [
            p for p in input_path.iterdir() if p.suffix.lower() in extensions
        ]
        if not files:
            logger.warning(f"No video/audio files found in {input_path}")
            return
    else:
        logger.error(f"Input path {input_path} does not exist.")
        raise typer.Exit(code=1)

    for file_path in files:
        try:
            logger.info(f"Processing {file_path}...")
            # Lazy import to avoid loading heavy libraries (Torch/Whisper) just for --help
            from .transcriber import transcribe_video
            
            subtitles = transcribe_video(
                str(file_path),
                output_language=output_language,
                use_vad=use_vad,
                model_size=model_size,
                high_quality=high_quality
            )

            # Determine output path
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                srt_path = output_dir / (file_path.stem + ".srt")
            else:
                srt_path = file_path.with_suffix(".srt")

            write_srt(subtitles, str(srt_path))
            print(f"Saved subtitles to {srt_path}")  # Force print to stdout
            logger.info(f"Saved subtitles to {srt_path}")

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            # Continue to next file


if __name__ == "__main__":
    app()
