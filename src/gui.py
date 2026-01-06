import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
from pathlib import Path
import os
from src.transcriber import transcribe_video
from src.utils import write_srt

class TranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper Translation Tool")
        self.root.geometry("800x450")

        self.input_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.model_size = tk.StringVar(value="base")
        self.output_language = tk.StringVar(value="en")
        self.use_vad = tk.BooleanVar(value=True)
        self.high_quality = tk.BooleanVar(value=False)
        
        self.progress_queue = queue.Queue()
        self.is_running = False

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input File
        ttk.Label(main_frame, text="Input:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(main_frame, textvariable=self.input_path, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=0, column=2, pady=5)
        ttk.Button(btn_frame, text="Files...", command=self._browse_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Folder...", command=self._browse_folder).pack(side=tk.LEFT, padx=2)

        # Output Directory
        ttk.Label(main_frame, text="Output Directory (Optional):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(main_frame, textvariable=self.output_dir, width=40).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Browse...", command=self._browse_output).grid(row=1, column=2, pady=5)

        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=20)

        # Model Size
        ttk.Label(options_frame, text="Model Size:").grid(row=0, column=0, sticky="w", padx=5)
        model_combo = ttk.Combobox(options_frame, textvariable=self.model_size, state="readonly")
        model_combo['values'] = ('tiny', 'base', 'small', 'medium', 'large')
        model_combo.grid(row=0, column=1, padx=5)

        # Language
        ttk.Label(options_frame, text="Target Language:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Entry(options_frame, textvariable=self.output_language, width=5).grid(row=0, column=3, padx=5)

        # VAD Checkbox
        ttk.Checkbutton(options_frame, text="Use VAD (Recommended)", variable=self.use_vad).grid(row=1, column=0, columnspan=2, sticky="w", pady=10, padx=5)

        # High Quality Checkbox
        ttk.Checkbutton(options_frame, text="High Quality Mode (Slower)", variable=self.high_quality).grid(row=1, column=2, columnspan=2, sticky="w", pady=10, padx=5)

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=3, column=0, columnspan=3, sticky="ew", pady=20)
        
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.grid(row=4, column=0, columnspan=3, sticky="w")

        # Start Button
        self.start_button = ttk.Button(main_frame, text="Start Transcription", command=self._start_transcription)
        self.start_button.grid(row=5, column=0, columnspan=3, pady=10)

    def _browse_files(self):
        filenames = filedialog.askopenfilenames(filetypes=[("Video/Audio files", "*.mp4 *.mkv *.avi *.mp3 *.wav *.flac *.m4a"), ("All files", "*.*")])
        if filenames:
            self.input_path.set(";".join(filenames))

    def _browse_folder(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.input_path.set(dirname)

    def _browse_output(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.output_dir.set(dirname)

    def _start_transcription(self):
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an input file.")
            return

        if self.is_running:
            return

        self.is_running = True
        self.start_button.config(state="disabled")
        self.status_label.config(text="Initializing...")
        self.progress_var.set(0)

        # Start background thread
        thread = threading.Thread(target=self._run_transcription_thread)
        thread.daemon = True
        thread.start()

        # Start polling for progress
        self.root.after(100, self._poll_progress)

    def _run_transcription_thread(self):
        try:
            raw_input = self.input_path.get()
            # Split by ; for multiple files
            paths = [Path(p.strip()) for p in raw_input.split(';') if p.strip()]
            
            all_files = []
            for p in paths:
                if p.is_dir():
                    # Add all video files in dir
                    extensions = {".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".flac", ".m4a"}
                    all_files.extend([f for f in p.iterdir() if f.suffix.lower() in extensions])
                elif p.is_file():
                    all_files.append(p)
            
            # Remove duplicates and sort
            all_files = sorted(list(set(all_files)))
            
            if not all_files:
                 self.progress_queue.put(("error", "No valid media files found."))
                 return

            total_files = len(all_files)
            processed_files = []

            for i, input_path in enumerate(all_files, 1):
                output_dir = Path(self.output_dir.get()) if self.output_dir.get() else input_path.parent
                
                def progress_callback(current, total):
                    self.progress_queue.put(("progress", (current, total, i, total_files, input_path.name)))

                self.progress_queue.put(("status", f"File {i}/{total_files}: {input_path.name} - Loading..."))
                
                subtitles = transcribe_video(
                    str(input_path),
                    output_language=self.output_language.get(),
                    use_vad=self.use_vad.get(),
                    model_size=self.model_size.get(),
                    high_quality=self.high_quality.get(),
                    progress_callback=progress_callback
                )

                self.progress_queue.put(("status", f"File {i}/{total_files}: {input_path.name} - Saving..."))
                
                srt_filename = input_path.stem + ".srt"
                final_output_path = output_dir / srt_filename
                write_srt(subtitles, str(final_output_path))
                processed_files.append(str(final_output_path))
            
            self.progress_queue.put(("done", "\n".join(processed_files)))

        except Exception as e:
            self.progress_queue.put(("error", str(e)))

    def _poll_progress(self):
        try:
            while True:
                msg_type, data = self.progress_queue.get_nowait()
                
                if msg_type == "progress":
                    current, total, file_idx, total_files, filename = data
                    if total > 0:
                        percentage = (current / total) * 100
                        self.progress_var.set(percentage)
                        self.status_label.config(text=f"File {file_idx}/{total_files}: {filename} - Segment {current}/{total}")
                
                elif msg_type == "status":
                    self.status_label.config(text=data)
                    if "Loading" in data:
                        self.progress_bar.config(mode='indeterminate')
                        self.progress_bar.start(10)
                    else:
                        self.progress_bar.stop()
                        self.progress_bar.config(mode='determinate')

                elif msg_type == "done":
                    self.is_running = False
                    self.start_button.config(state="normal")
                    self.progress_bar.stop()
                    self.progress_var.set(100)
                    self.status_label.config(text="Completed!")
                    messagebox.showinfo("Success", f"Subtitles saved to:\n{data}")
                    return

                elif msg_type == "error":
                    self.is_running = False
                    self.start_button.config(state="normal")
                    self.progress_bar.stop()
                    self.status_label.config(text="Error occurred")
                    messagebox.showerror("Error", f"An error occurred:\n{data}")
                    return

        except queue.Empty:
            pass
        
        if self.is_running:
            self.root.after(100, self._poll_progress)

def main():
    root = tk.Tk()
    app = TranslationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
