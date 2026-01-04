Build a python CLI application that creates SRT subtitles from a given video file using Whisper (https://github.com/openai/whisper) translation model and the silero-vad (https://github.com/snakers4/silero-vad) library for voice activity detection.

Ensure that the application:

- Accepts a video file as input
- Accepts an output language for the subtitles and actually translates the audio to that language
- Generates SRT subtitle files with accurate timestamps
- Handles errors gracefully and provides informative messages to the user
- Leverages the whisper model for accurate transcription and translation
- Uses silero-vad to detect speech segments in the audio. Evaluate if this is necessary for the implementation
- Allow for single file processing and batch processing of multiple video files in a directory
- Provide a help command to guide users on how to use the application
- use flake8 for code style enforcement
- use typer to build the CLI application
