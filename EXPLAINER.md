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

---

## Packaging Strategy (PyInstaller)

We used **PyInstaller** to package this Python application into a single, standalone binary executable.

### How it Works

1. **Analysis:** PyInstaller analyzes `run.py` and recursively finds all the `import` statements to discover every library the application needs (Typer, Torch, Whisper, NumPy, etc.).
2. **Collection:** It collects the Python interpreter itself (from your virtual environment), all the discovered library files (`.py`, `.so`, `.dylib`), and the script's bytecode.
3. **Bundling:**
    * We used the `--onefile` mode. This compresses all the collected files into a single archive appended to a bootloader executable.
4. **Execution:**
    * When you run the final binary (`dist/translation-tool`), the bootloader runs first.
    * It creates a temporary folder in your system's temp directory (e.g., `_MEIxxxxxx`).
    * It unpacks all the bundled libraries and the Python interpreter into that temporary folder.
    * It executes your script using that unpacked environment.

### Why this strategy?

* **Portability:** The user does not need to have Python, PyTorch, or any libraries installed. They just need the binary.
* **Simplicity:** It turns a complex environment with dozens of dependencies into a single file that can be copied to `/usr/local/bin`.

### The Build Command

The command used was:

```bash
pyinstaller --onefile --name translation-tool run.py
```

* `--onefile`: Create a single executable file instead of a folder.
* `--name`: Name the output binary `translation-tool`.

---

## How to Run

### 1. Using the Source Code (For Developers)

If you want to modify the code, run it using the wrapper script:

```bash
# Make sure it's executable
chmod +x run.py

# Run it
./run.py path/to/video.mp4
```

### 2. Using the Binary (For Users)

This is the standalone file located in `dist/`.

```bash
# Run directly
./dist/translation-tool path/to/video.mp4

# Or install it to your path
sudo mv dist/translation-tool /usr/local/bin/
translation-tool path/to/video.mp4
```

### Prerequisites

* **FFmpeg:** The application (specifically the `whisper` and `pydub`/`ffmpeg-python` underlying libraries) requires `ffmpeg` to be installed on the system to process audio files.
  * macOS: `brew install ffmpeg`
  * Linux: `sudo apt install ffmpeg`
