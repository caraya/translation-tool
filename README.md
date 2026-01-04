# Translation Tool

A Python CLI application that creates SRT subtitles from a given video file using Whisper translation model and the silero-vad library for voice activity detection.

## Prerequisites

* **Python 3.10+**
* **FFmpeg**: Required for audio processing.
  * macOS: `brew install ffmpeg`
  * Linux: `sudo apt install ffmpeg`

## Installation

1. Clone the repository:

    ```bash
    git clone <repository-url>
    cd translation-tool
    ```

2. Set up the virtual environment and install dependencies:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

## Usage

### Running from Source (Development)

The easiest way to run the tool is using the provided wrapper script. It automatically handles the virtual environment for you.

```bash
# Make the script executable (first time only)
chmod +x run.py

# Run on a single video
./run.py path/to/video.mp4

# Run on a folder of videos
./run.py path/to/video_folder

# View all options
./run.py --help
```

### Building a Standalone Executable

You can package the application into a single binary file that doesn't require Python to be installed on the target machine.

1. Ensure `pyinstaller` is installed:

    ```bash
    pip install pyinstaller
    ```

2. Build the binary:

    ```bash
    pyinstaller --onefile --name translation-tool run.py
    ```

3. The executable will be created in the `dist/` directory. You can run it directly:

    ```bash
    ./dist/translation-tool path/to/video.mp4
    ```

4. (Optional) Move it to your PATH to run it from anywhere:

    ```bash
    sudo mv dist/translation-tool /usr/local/bin/
    ```

## Options

* `--model-size`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large`). Default: `base`.
* `--output-language`: Target language code (e.g., `en`). Default: `en`.
* `--use-vad / --no-use-vad`: Enable/disable Silero VAD for speech detection. Default: `True`.
* `--output-dir`: Directory to save SRT files. Defaults to the input directory.

## Improving Translation Quality

If you find the translation quality insufficient, try the following strategies:

### 1. Use a Larger Model

The default `base` model is optimized for speed. For better accuracy, especially with translation, use a larger model:

```bash
./run.py --model-size large path/to/video.mp4
```

*Available sizes:* `tiny`, `base`, `small`, `medium`, `large`.

*Note:* Larger models require more RAM and will take significantly longer to process.

### 2. Disable VAD

Voice Activity Detection (VAD) chops audio into segments to skip silence. Sometimes this cuts off context needed for accurate translation. Disabling it can improve coherence:

```bash
./run.py --no-use-vad path/to/video.mp4
```

*Tradeoff:* Disabling VAD may increase processing time and can sometimes lead to "hallucinations" (text generated during silence).
