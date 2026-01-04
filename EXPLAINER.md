# Project Explainer & Code Walkthrough

This document provides a detailed technical overview of the Translation Tool, explaining the purpose of each file, the design decisions behind the code, and the strategy used to package the application into a standalone executable.

## Code Walkthrough

### 1. `src/main.py` (CLI Entry Point)

**Purpose:** This is the main entry point of the application. It handles the Command Line Interface (CLI) using the `typer` library.

**Key Responsibilities:**

* **Argument Parsing:** Defines the commands, arguments (like input path), and options (like model size, language).
* **Input Validation:** Checks if the input path is a valid file or directory. If it's a directory, it filters for common video/audio extensions (`.mp4`, `.mkv`, etc.).
* **Orchestration:** It acts as the controller. It iterates through the found files, calls the transcription logic (`transcribe_video`), and then calls the saving logic (`write_srt`).
* **Logging:** Sets up the logging configuration to provide feedback to the user during execution.

**Why this design?**

Using `typer` makes the CLI easy to maintain and self-documenting (it generates the `--help` menu automatically). Separating the CLI logic from the core transcription logic ensures that the core logic can be reused or tested independently of the command line interface.

### 2. `src/transcriber.py` (Core Logic)

**Purpose:** This file contains the heavy lifting of the application: the integration with OpenAI's Whisper model and the logic to combine it with Voice Activity Detection (VAD).

**Key Responsibilities:**

* **Model Loading:** Loads the Whisper model based on the user's selected size (`tiny`, `base`, `large`, etc.). It automatically selects the device (`cuda` for GPU or `cpu`).
* **Task Determination:** Decides whether to perform "translation" (to English) or "transcription" (keeping the original language) based on the user's input. *Note: Whisper's translation capability is primarily designed to translate TO English.*
* **VAD Integration:**
  * If `use_vad` is True, it first calls `get_speech_timestamps` to find exactly *where* speech occurs in the video.
  * It then iterates through these timestamps, extracts the specific audio segment, and feeds *only that segment* to Whisper.
  * This improves accuracy by preventing Whisper from hallucinating subtitles during long periods of silence or background noise.
* **Standard Transcription:** If VAD is disabled, it falls back to Whisper's default full-file transcription.

**Why this design?**
Splitting the video into segments based on VAD before sending it to Whisper is a common optimization pattern. It reduces processing time (by skipping silence) and improves quality.

### 3. `src/vad.py` (Voice Activity Detection)

**Purpose:** This module is a dedicated wrapper for the Silero VAD library.

**Key Responsibilities:**

* **Model Loading:** It uses `torch.hub.load` to download and load the `silero-vad` model directly from GitHub. This avoids complex dependency management issues often found with the pip package version of Silero.
* **Timestamp Extraction:** It takes an audio path, processes it, and returns a list of start/end timestamps where speech is detected.

**Why this design?**

Isolating the VAD logic into its own file keeps the `transcriber.py` clean. Using `torch.hub` is a robust way to get the latest model without worrying about local package version conflicts.

### 4. `src/utils.py` (Helpers)

**Purpose:** Contains utility functions, primarily for file formatting.

**Key Responsibilities:**

* **`format_timestamp`:** Converts seconds (float) into the specific time format required by SRT files (`HH:MM:SS,mmm`).
* **`write_srt`:** Takes the list of subtitle dictionaries and writes them to a text file in the standard SubRip (.srt) format.

**Why this design?**

File format details shouldn't clutter the main application logic. If we wanted to support VTT or other formats later, we would just add new functions here.

### 5. `run.py` (Execution Wrapper)

**Purpose:** A simple script to launch the application.

**Key Responsibilities:**

* **Import Fix:** It imports `app` from `src.main` and runs it.
* **Shebang:** It includes a specific shebang line pointing to the project's virtual environment. This ensures that even if you run `./run.py` from a shell where the venv isn't active, it will still use the correct Python interpreter and dependencies.
* **Multiprocessing Support:** It calls `multiprocessing.freeze_support()` to ensure that the application behaves correctly when spawned as a background process (e.g., by PyTorch data loaders) in a frozen/packaged state.

---

## Improving Translation Quality

Achieving high-quality translations with Whisper involves balancing accuracy against performance. Here are the primary strategies and their tradeoffs:

### 1. Increasing Model Size

The most direct way to improve quality is to use a larger model.

* **Strategy:** Switch from the default `base` model to `small`, `medium`, or `large`.
* **Tradeoff:** Larger models are significantly slower and require more memory (RAM/VRAM).
  * `base`: Fast, decent for clear English, struggles with accents/translation.
  * `small`: Good balance for many use cases.
  * `medium`: High quality, much slower.
  * `large`: Best quality, very slow, requires significant resources.

### 2. Disabling VAD (Voice Activity Detection)

By default, this tool uses Silero VAD to segment audio before sending it to Whisper.

* **The Issue:** VAD might cut audio too aggressively during short pauses within a sentence. Since translation relies heavily on context, splitting a sentence in half can result in nonsensical translations.
* **Strategy:** Use the `--no-use-vad` flag. This passes larger chunks of audio to Whisper, preserving context.
* **Tradeoff:** Without VAD, Whisper is more prone to "hallucinations" (generating text during silence) and processing might be slower as it processes silent segments.

### 3. Prompt Engineering (Advanced)

Whisper accepts an `initial_prompt` to provide context.

* **Strategy:** Providing a prompt like "This is a medical lecture about cardiology" helps the model resolve ambiguous terms.
* **Tradeoff:** Requires knowing the content beforehand. (Note: This feature requires code modification to expose the `initial_prompt` parameter in the CLI).

---

### Packaging Strategy (PyInstaller)

We used **PyInstaller** to package this Python application.

**Update:** We switched from `--onefile` to `--onedir` mode to improve startup performance.

* **--onefile (Old):** Compressed everything into a single binary. Slow startup because it had to unpack >1GB of data to a temporary folder on every run.
* **--onedir (New):** Creates a directory containing the executable and all dependencies. Fast startup because files are already unpacked.

### How it Works

1. **Analysis:** PyInstaller analyzes `run.py` and recursively finds all the `import` statements.
2. **Collection:** It collects the Python interpreter and all libraries.
3. **Bundling:** It places them into a `dist/translation-tool/` directory.
4. **Execution:** The binary `dist/translation-tool/translation-tool` runs immediately using the libraries in its own folder.

### The Build Command

```bash
pyinstaller --onedir --name translation-tool run.py
```

---

## How to Run

### 1. Using the Source Code (For Developers)

```bash
chmod +x run.py
./run.py path/to/video.mp4
```

### 2. Using the Binary (For Users)

**Build:**

```bash
pyinstaller --onedir --name translation-tool run.py
```

**Install:**

We provided an `install.sh` script to handle the installation to `/usr/local/lib` (for the files) and `/usr/local/bin` (for the symlink).

```bash
sudo ./install.sh
```

**Run:**

```bash
translation-tool path/to/video.mp4
```

### Prerequisites

* **FFmpeg:** The application (specifically the `whisper` and `pydub`/`ffmpeg-python` underlying libraries) requires `ffmpeg` to be installed on the system to process audio files.
  * macOS: `brew install ffmpeg`
  * Linux: `sudo apt install ffmpeg`
