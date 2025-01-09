import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
import subprocess
import os
import threading
import queue
import re
import json
import traceback

# ======== Utility Functions ========

def check_ffmpeg():
    try:
        version_result = subprocess.run(
            ["ffmpeg", "-version"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        encoders_result = subprocess.run(
            ["ffmpeg", "-encoders"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        encoders_output = encoders_result.stdout.decode()
        codec = "hevc" if "hevc_nvenc" in encoders_output else "h264"
        if codec == "h264":
            messagebox.showerror(
                "NVENC HEVC Not Available",
                "Your system doesn't support NVENC HEVC encoding. Falling back to H264."
            )
        return codec
    except FileNotFoundError:
        messagebox.showerror(
            "FFmpeg Not Found",
            "FFmpeg is required but not installed. Please install it and add to PATH."
        )
        return False

def get_video_resolution(file_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,codec_name", "-of", "json", file_path],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        info = json.loads(result.stdout)
        stream = info.get("streams", [{}])[0]
        return int(stream.get("width", 0)), int(stream.get("height", 0)), stream.get("codec_name", "")
    except Exception:
        return 0, 0, ""

# ======== Core Transcoding Logic ========

def build_ffmpeg_command(app, file_path, output_path):
    """Builds the FFmpeg command based on user settings and profiles."""
    scale_enabled = app.downscale_var.get()
    codec_support = app.codec_support
    output_format = app.output_format_var.get()
    audio_codec = app.audio_codec_var.get()
    audio_bitrate = app.audio_bitrate_var.get()
    audio_sample_rate = app.audio_sample_rate_var.get()
    audio_channels = app.audio_channels_var.get()

    width, height, input_codec = get_video_resolution(file_path)

    command = [
        "ffmpeg",
        "-hwaccel_output_format", "cuda",
        "-extra_hw_frames", "3",
        "-thread_queue_size", "1024",
        "-i", file_path
    ]

    # Video Encoding Settings
    if codec_support == "hevc":
        command.extend([
            "-c:v", "hevc_nvenc",
            "-preset", "p2",
            "-tune", "hq",
            "-rc", "vbr",
            "-cq", "19",
            "-qmin", "1",
            "-qmax", "51",
            "-b:v", "20M",
            "-maxrate", "30M",
            "-bufsize", "40M",
            "-spatial-aq", "1",
            "-temporal-aq", "1",
            "-refs", "3",
            "-g", "250",
            "-bf", "3"
        ])
    else:
        command.extend([
            "-c:v", "h264_nvenc",
            "-preset", "p2",
            "-tune", "hq",
            "-rc", "vbr",
            "-cq", "19",
            "-qmin", "1",
            "-qmax", "51",
            "-b:v", "20M",
            "-maxrate", "30M",
            "-bufsize", "40M",
            "-spatial-aq", "1",
            "-temporal-aq", "1",
            "-refs", "3",
            "-g", "250",
            "-bf", "3"
        ])

    # Audio Settings
    command.extend([
        "-c:a", "copy" if input_codec == "aac" and audio_codec == "aac" else audio_codec,
        "-b:a", f"{audio_bitrate}k",
        "-ar", str(audio_sample_rate),
        "-ac", str(audio_channels)
    ])

    # Output Format and Common Settings
    command.extend([
        "-f", output_format,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-map_metadata", "0",
        "-map", "0"
    ])

    if scale_enabled:
        target_width = app.scale_width_var.get()
        target_height = app.scale_height_var.get()
        command.extend(["-vf", f"scale={target_width}:{target_height}"])

    command.append(output_path)
    return command

def remux_video(app, file_path, output_queue):
    output_folder = app.output_folder if app.output_folder else os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0] + "_transcoded." + app.output_format_var.get()
    output_path = os.path.join(output_folder, base_name)
    command = build_ffmpeg_command(app, file_path, output_path)

    try:
        print("Executing FFmpeg command:", " ".join(command))
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        app.transcoding_processes[file_path] = process

        stderr_output = []
        for line in process.stderr:
            stderr_output.append(line)
            print(line, end='')

        process.wait()
        if process.returncode == 0:
            output_queue.put((file_path, output_path, "Success"))
        else:
            error_message = "FFmpeg Error:\n" + "\n".join(stderr_output[-5:])
            output_queue.put((file_path, None, f"Error: {error_message}"))
    except Exception as e:
        output_queue.put((file_path, None, f"Error: {str(e)}\n{traceback.format_exc()}"))
    finally:
        if file_path in app.transcoding_processes:
            del app.transcoding_processes[file_path]

def process_queue(remux_queue, output_queue, stop_event, app):
    while not stop_event.is_set():
        try:
            file_path = remux_queue.get(timeout=1)
            width, height, _ = get_video_resolution(file_path)
            if width < 1280 or height < 720:
                warning_msg = f"Warning: {os.path.basename(file_path)} is below HD resolution. Consider enabling scaling."
                output_queue.put((file_path, None, warning_msg))

            remux_video(app, file_path, output_queue)
            remux_queue.task_done()
        except queue.Empty:
            continue

# ======== Main Application Class ========

class RemuxTool(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.codec_support = check_ffmpeg()
        if not self.codec_support:
            self.quit()

        # Initialize main window properties
        self.title("Video Transcoder - Advanced")
        self.resizable(True, True)
        self.geometry("1000x700")
        self.configure(bg="#2e2e2e")
        
        # Queues and threading
        self.remux_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.transcoding_processes = {}

        # Variables for user-configurable settings
        self.downscale_var = tk.BooleanVar(value=False)
        self.output_format_var = tk.StringVar(value="mp4")
        self.audio_codec_var = tk.StringVar(value="aac")
        self.audio_bitrate_var = tk.IntVar(value=192)
        self.audio_sample_rate_var = tk.IntVar(value=48000)
        self.audio_channels_var = tk.IntVar(value=2)
        self.scale_width_var = tk.IntVar(value=1920)
        self.scale_height_var = tk.IntVar(value=1080)

        # Output folder
        self.output_folder = None

        # Setup UI Components
        self.setup_ui()
        self.after(100, self.check_output_queue)

    def setup_ui(self):
        # --- Top Frame ---
        top_frame = tk.Frame(self, bg="#2e2e2e")
        top_frame.pack(fill='x', padx=10, pady=10)
        top_label = tk.Label(top_frame, text="Drag and drop videos or use 'Browse Files'", bg="#2e2e2e", fg="white", font=("Arial", 14))
        top_label.pack(fill='x')

        # --- Middle Frame ---
        middle_frame = tk.Frame(self, bg="#2e2e2e")
        middle_frame.pack(fill='both', expand=True, padx=10, pady=10)
        middle_frame.rowconfigure(0, weight=1)
        middle_frame.columnconfigure(0, weight=1)

        scrollbar = tk.Scrollbar(middle_frame)
        scrollbar.grid(row=0, column=1, sticky='ns')

        self.queue_listbox = tk.Listbox(middle_frame, bg="#1e1e1e", fg="white", font=("Arial", 12), selectmode=tk.BROWSE, yscrollcommand=scrollbar.set)
        self.queue_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.queue_listbox.yview)

        # --- Bottom Frame ---
        bottom_frame = tk.Frame(self, bg="#2e2e2e")
        bottom_frame.pack(fill='x', padx=10, pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", mode="determinate")
        self.progress.grid(row=0, column=0, columnspan=6, sticky="ew", pady=5)

        # Downscale checkbox and resolution inputs
        self.downscale_checkbox = tk.Checkbutton(bottom_frame, text="Force scale to custom resolution", variable=self.downscale_var, bg="#2e2e2e", fg="white", font=("Arial", 12))
        self.downscale_checkbox.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        tk.Label(bottom_frame, text="Width:", bg="#2e2e2e", fg="white").grid(row=1, column=2)
        tk.Entry(bottom_frame, textvariable=self.scale_width_var, width=5).grid(row=1, column=3)
        tk.Label(bottom_frame, text="Height:", bg="#2e2e2e", fg="white").grid(row=1, column=4)
        tk.Entry(bottom_frame, textvariable=self.scale_height_var, width=5).grid(row=1, column=5)

        # Output format selection
        tk.Label(bottom_frame, text="Format:", bg="#2e2e2e", fg="white").grid(row=2, column=0)
        format_menu = ttk.Combobox(bottom_frame, textvariable=self.output_format_var, values=["mp4", "mkv", "mov", "avi"], width=10)
        format_menu.grid(row=2, column=1)

        # Audio codec selection
        tk.Label(bottom_frame, text="Audio Codec:", bg="#2e2e2e", fg="white").grid(row=2, column=2)
        audio_codec_menu = ttk.Combobox(bottom_frame, textvariable=self.audio_codec_var, values=["aac", "opus", "vorbis", "flac"], width=10)
        audio_codec_menu.grid(row=2, column=3)

        # Audio bitrate
        tk.Label(bottom_frame, text="Audio Bitrate (kbps):", bg="#2e2e2e", fg="white").grid(row=3, column=0)
        tk.Entry(bottom_frame, textvariable=self.audio_bitrate_var, width=7).grid(row=3, column=1)

        # Audio sample rate
        tk.Label(bottom_frame, text="Sample Rate:", bg="#2e2e2e", fg="white").grid(row=3, column=2)
        tk.Entry(bottom_frame, textvariable=self.audio_sample_rate_var, width=7).grid(row=3, column=3)

        # Audio channels
        tk.Label(bottom_frame, text="Channels:", bg="#2e2e2e", fg="white").grid(row=3, column=4)
        tk.Entry(bottom_frame, textvariable=self.audio_channels_var, width=7).grid(row=3, column=5)

        # Output folder selection
        self.output_folder_button = tk.Button(bottom_frame, text="Select Output Folder", command=self.open_output_folder_dialog)
        self.output_folder_button.grid(row=4, column=0, padx=5, pady=5, sticky="w")

        self.output_folder_label = tk.Label(bottom_frame, text="No folder selected", bg="#2e2e2e", fg="white", font=("Arial", 10))
        self.output_folder_label.grid(row=4, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        # Action buttons
        self.browse_button = tk.Button(bottom_frame, text="Browse Files", command=self.open_file_dialog)
        self.browse_button.grid(row=5, column=0, padx=5, pady=10, sticky="w")

        self.start_button = tk.Button(bottom_frame, text="Start Transcoding", command=self.start_transcoding)
        self.start_button.grid(row=5, column=1, padx=5, pady=10, sticky="w")

        self.stop_button = tk.Button(bottom_frame, text="Stop Transcoding", command=self.stop_transcoding)
        self.stop_button.grid(row=5, column=2, padx=5, pady=10, sticky="w")

        self.clear_button = tk.Button(bottom_frame, text="Clear Queue", command=self.clear_queue)
        self.clear_button.grid(row=5, column=3, padx=5, pady=10, sticky="e")

        # Drag and drop setup
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.on_drop)

    # ======== Event Handlers and Threading ========
    def start_worker_thread(self):
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.stop_event.clear()
            self.worker_thread = threading.Thread(
                target=process_queue,
                args=(self.remux_queue, self.output_queue, self.stop_event, self),
                daemon=True
            )
            self.worker_thread.start()

    def on_drop(self, event):
        file_paths = self.parse_dropped_files(event.data)
        for file_path in file_paths:
            if file_path:
                self.queue_listbox.insert(tk.END, f"Queued: {os.path.basename(file_path)}")
                self.remux_queue.put(file_path)

    def parse_dropped_files(self, data):
        return re.findall(r'\{(.*?)\}', data) or data.split()

    def open_file_dialog(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv *.mxf *.webm *.flv *.ts")])
        for file_path in file_paths:
            self.queue_listbox.insert(tk.END, f"Queued: {os.path.basename(file_path)}")
            self.remux_queue.put(file_path)

    def open_output_folder_dialog(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_folder_label.config(text=self.output_folder)
            self.queue_listbox.insert(tk.END, f"Output Folder Set: {self.output_folder}")

    def start_transcoding(self):
        if self.remux_queue.empty():
            messagebox.showinfo("No Files", "There are no files in the queue to transcode.")
        else:
            messagebox.showinfo("Transcoding Started", "Transcoding has started.")
            self.start_worker_thread()

    def stop_transcoding(self):
        for file_path, process in list(self.transcoding_processes.items()):
            process.terminate()
            self.queue_listbox.insert(tk.END, f"Stopped: {os.path.basename(file_path)}")
            del self.transcoding_processes[file_path]

    def clear_queue(self):
        with self.remux_queue.mutex:
            self.remux_queue.queue.clear()
        self.queue_listbox.delete(0, tk.END)
        self.progress["value"] = 0

    def check_output_queue(self):
        while not self.output_queue.empty():
            file_path, output_path, status = self.output_queue.get()
            if status and status.startswith("Warning:"):
                self.queue_listbox.insert(tk.END, status)
            elif status == "Success":
                self.queue_listbox.insert(tk.END, f"Completed: {os.path.basename(file_path)} -> {output_path}")
            elif status and status.startswith("Error:"):
                self.queue_listbox.insert(tk.END, f"Error processing: {os.path.basename(file_path)}\n{status}")
            else:
                self.queue_listbox.insert(tk.END, f"Processed: {os.path.basename(file_path)}")

            total_tasks = self.remux_queue.qsize() + self.output_queue.qsize()
            completed_tasks = self.queue_listbox.size()
            if total_tasks + completed_tasks > 0:
                self.progress["value"] = (completed_tasks / (total_tasks + completed_tasks)) * 100
            else:
                self.progress["value"] = 0

        self.after(100, self.check_output_queue)

    # ======== Cleanup ========
    def on_close(self):
        self.stop_event.set()
        self.stop_transcoding()
        self.destroy()

# ======== Entry Point ========
if __name__ == "__main__":
    app = RemuxTool()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
