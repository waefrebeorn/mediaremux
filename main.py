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

# Check if ffmpeg is installed and check encoder support
def check_ffmpeg():
    try:
        # Check ffmpeg version
        version_result = subprocess.run(
            ["ffmpeg", "-version"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        # Check NVENC HEVC support
        encoders_result = subprocess.run(
            ["ffmpeg", "-encoders"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        encoders_output = encoders_result.stdout.decode()
        if "hevc_nvenc" not in encoders_output:
            messagebox.showerror(
                "NVENC HEVC Not Available",
                "Your system doesn't support NVENC HEVC encoding. Falling back to H264."
            )
            return "h264"
            
        return "hevc"
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

def remux_video(app, file_path, output_queue):
    scale_enabled = app.downscale_var.get()
    output_folder = app.output_folder if app.output_folder else os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0] + "_transcoded.mp4"
    output_path = os.path.join(output_folder, base_name)

    # Get input codec and resolution
    width, height, input_codec = get_video_resolution(file_path)

    # Base command with optimized settings
    command = [
        "ffmpeg",
        "-hwaccel_output_format", "cuda",  # Ensure CUDA output format
        "-extra_hw_frames", "3",           # Additional hardware frames
        "-thread_queue_size", "1024",      # Increase thread queue size
        "-i", file_path
    ]

    # Add encoding settings based on codec support
    if app.codec_support == "hevc":
        command.extend([
            "-c:v", "hevc_nvenc",
            "-preset", "p2",               # Fast preset
            "-tune", "hq",                 # High quality tuning
            "-rc", "vbr",                  # Variable bitrate
            "-cq", "19",                   # Constant quality factor
            "-qmin", "1",                  # Minimum quantizer
            "-qmax", "51",                 # Maximum quantizer
            "-b:v", "20M",                 # Base video bitrate
            "-maxrate", "30M",             # Maximum bitrate
            "-bufsize", "40M",             # VBV buffer size
            "-spatial-aq", "1",            # Enable spatial AQ
            "-temporal-aq", "1",           # Enable temporal AQ
            "-refs", "3",                  # Number of reference frames
            "-g", "250",                   # Keyframe interval
            "-bf", "3"                     # Number of B-frames
        ])
    else:
        # Fallback to H264 with optimized settings
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

    # Audio settings - copy if already AAC, otherwise encode
    command.extend([
        "-c:a", "copy" if input_codec == "aac" else "aac",
        "-b:a", "192k",
        "-ar", "48000"                     # Set sample rate
    ])

    # Common settings
    command.extend([
        "-pix_fmt", "yuv420p",            # Standard pixel format
        "-movflags", "+faststart",         # Enable fast start
        "-map_metadata", "0",              # Copy metadata
        "-map", "0"                        # Map all streams
    ])

    if scale_enabled:
        command.extend(["-vf", "scale=1920:1080"])

    command.append(output_path)

    try:
        # Add debug logging
        print("Executing FFmpeg command:", " ".join(command))
        
        # Start the ffmpeg process with stderr pipe for progress
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Store the process for potential termination
        app.transcoding_processes[file_path] = process
        
        # Read stderr for progress and errors
        stderr_output = []
        for line in process.stderr:
            stderr_output.append(line)
            print(line, end='')  # Print progress in real-time
            
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

            # Check resolution and prepare a warning message if needed
            width, height, _ = get_video_resolution(file_path)
            if width < 1280 or height < 720:
                warning_msg = f"Warning: {os.path.basename(file_path)} is below HD resolution. Consider enabling scaling."
                output_queue.put((file_path, None, warning_msg))

            remux_video(app, file_path, output_queue)
            remux_queue.task_done()
        except queue.Empty:
            continue

class RemuxTool(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.codec_support = check_ffmpeg()
        if not self.codec_support:
            self.quit()
        self.title("Video Transcoder - HEVC Game Stream Optimized")
        
        # Make the window resizable
        self.resizable(True, True)
        
        # Set initial geometry
        self.geometry("800x600")
        self.configure(bg="#2e2e2e")

        # Configure grid layout for the main window
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Initialize queues and threading
        self.remux_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.stop_event = threading.Event()

        # Thread for processing queue
        self.worker_thread = None

        # Dictionary to store running processes for stopping
        self.transcoding_processes = {}

        # Top Frame for instructions
        top_frame = tk.Frame(self, bg="#2e2e2e")
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)

        self.label = tk.Label(
            top_frame,
            text="Drag and drop your videos here or use 'Browse Files'",
            bg="#2e2e2e", fg="white", font=("Arial", 14)
        )
        self.label.pack(fill='x')

        # Middle Frame for Listbox and Scrollbar
        middle_frame = tk.Frame(self, bg="#2e2e2e")
        middle_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        middle_frame.grid_rowconfigure(0, weight=1)
        middle_frame.grid_columnconfigure(0, weight=1)

        # Add scrollbar to the listbox
        scrollbar = tk.Scrollbar(middle_frame)
        scrollbar.grid(row=0, column=1, sticky='ns')

        self.queue_listbox = tk.Listbox(
            middle_frame,
            bg="#1e1e1e",
            fg="white",
            font=("Arial", 12),
            selectmode=tk.BROWSE,
            yscrollcommand=scrollbar.set
        )
        self.queue_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.queue_listbox.yview)

        # Bottom Frame for controls
        bottom_frame = tk.Frame(self, bg="#2e2e2e")
        bottom_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(1, weight=1)

        # Progress bar
        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", mode="determinate")
        self.progress.grid(row=0, column=0, columnspan=4, sticky="ew", pady=5)

        # Downscale checkbox
        self.downscale_var = tk.BooleanVar(value=False)
        self.downscale_checkbox = tk.Checkbutton(
            bottom_frame,
            text="Force scale to 1080p",
            variable=self.downscale_var,
            bg="#2e2e2e", fg="white",
            font=("Arial", 12)
        )
        self.downscale_checkbox.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Output folder selection
        self.output_folder_button = tk.Button(
            bottom_frame,
            text="Select Output Folder",
            command=self.open_output_folder_dialog
        )
        self.output_folder_button.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.output_folder_label = tk.Label(
            bottom_frame,
            text="No folder selected",
            bg="#2e2e2e",
            fg="white",
            font=("Arial", 10)
        )
        self.output_folder_label.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        # Action buttons
        self.browse_button = tk.Button(
            bottom_frame,
            text="Browse Files",
            command=self.open_file_dialog
        )
        self.browse_button.grid(row=3, column=0, padx=5, pady=10, sticky="w")

        self.start_button = tk.Button(
            bottom_frame,
            text="Start Transcoding",
            command=self.start_transcoding
        )
        self.start_button.grid(row=3, column=1, padx=5, pady=10, sticky="w")

        self.stop_button = tk.Button(
            bottom_frame,
            text="Stop Transcoding",
            command=self.stop_transcoding
        )
        self.stop_button.grid(row=3, column=2, padx=5, pady=10, sticky="w")

        self.clear_button = tk.Button(
            bottom_frame,
            text="Clear Queue",
            command=self.clear_queue
        )
        self.clear_button.grid(row=3, column=3, padx=5, pady=10, sticky="e")

        # Drag and drop setup
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.on_drop)

        self.output_folder = None

        if not check_ffmpeg():
            self.quit()

        self.after(100, self.check_output_queue)

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
        # Handle paths with spaces which are enclosed in {}
        return re.findall(r'\{(.*?)\}', data) or data.split()

    def open_file_dialog(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv *.mxf")]
        )
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
            messagebox.showinfo("Transcoding Started", "Transcoding has started. Please wait for it to complete.")
            self.start_worker_thread()

    def stop_transcoding(self):
        # Terminate all active transcoding processes
        for file_path, process in list(self.transcoding_processes.items()):
            process.terminate()
            self.queue_listbox.insert(tk.END, f"Stopped: {os.path.basename(file_path)}")
            del self.transcoding_processes[file_path]

    def clear_queue(self):
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

    def on_close(self):
        self.stop_event.set()
        # Attempt to terminate any remaining processes
        self.stop_transcoding()
        self.destroy()

if __name__ == "__main__":
    app = RemuxTool()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()