import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
import subprocess
import os
from tkinter import messagebox, filedialog
import threading
import queue
import re

# Check if ffmpeg is installed
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        messagebox.showerror("FFmpeg Not Found", "FFmpeg is required but not installed. Please install it and add to PATH.")
        return False

# Function to remux the video
def remux_video(file_path, output_queue):
    if file_path.endswith((".mp4", ".mov", ".avi")):
        output_path = os.path.splitext(file_path)[0] + "_remuxed.mkv"
        command = ["ffmpeg", "-i", f"{file_path}", "-c", "copy", f"{output_path}"]
        try:
            subprocess.run(command, check=True)
            output_queue.put((file_path, output_path, "Success"))
        except subprocess.CalledProcessError:
            output_queue.put((file_path, None, "Error"))
    else:
        output_queue.put((file_path, None, "Invalid File"))

# Background worker to process the queue
def process_queue(remux_queue, output_queue, stop_event):
    while not stop_event.is_set():
        try:
            file_path = remux_queue.get(timeout=1)
            remux_video(file_path, output_queue)
            remux_queue.task_done()
        except queue.Empty:
            continue

# Main GUI class
class RemuxTool(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Remux Tool for DaVinci Resolve")
        self.geometry("500x400")
        self.configure(bg="#2e2e2e")

        # Queue and threading setup
        self.remux_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=process_queue, args=(self.remux_queue, self.output_queue, self.stop_event), daemon=True)
        self.worker_thread.start()

        # GUI elements
        self.label = tk.Label(self, text="Drag and drop your videos here or use 'Browse Files'", bg="#2e2e2e", fg="white", font=("Arial", 14))
        self.label.pack(pady=10)

        self.queue_listbox = tk.Listbox(self, width=60, height=12, bg="#1e1e1e", fg="white")
        self.queue_listbox.pack(pady=10)

        # Drag and drop setup
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.on_drop)

        # Button to open file dialog for large files
        self.browse_button = tk.Button(self, text="Browse Files", command=self.open_file_dialog)
        self.browse_button.pack(pady=10)

        if not check_ffmpeg():
            self.quit()

        # Polling for processing results
        self.after(100, self.check_output_queue)

    def on_drop(self, event):
        file_paths = self.parse_dropped_files(event.data)
        for file_path in file_paths:
            if file_path:  # Ensure it's a valid path
                self.queue_listbox.insert(tk.END, f"Queued: {os.path.basename(file_path)}")
                self.remux_queue.put(file_path)

    def parse_dropped_files(self, data):
        # Use regex to parse each file path individually, even with spaces and special characters
        return re.findall(r'\{(.*?)\}', data)

    def open_file_dialog(self):
        # Allow user to select multiple files through file dialog
        file_paths = filedialog.askopenfilenames(filetypes=[("Video Files", "*.mp4 *.mov *.avi")])
        for file_path in file_paths:
            self.queue_listbox.insert(tk.END, f"Queued: {os.path.basename(file_path)}")
            self.remux_queue.put(file_path)

    def check_output_queue(self):
        while not self.output_queue.empty():
            file_path, output_path, status = self.output_queue.get()
            if status == "Success":
                self.queue_listbox.insert(tk.END, f"Completed: {os.path.basename(file_path)} -> {output_path}")
            elif status == "Error":
                self.queue_listbox.insert(tk.END, f"Error processing: {os.path.basename(file_path)}")
            else:
                self.queue_listbox.insert(tk.END, f"Invalid File: {os.path.basename(file_path)}")
        self.after(100, self.check_output_queue)

    def on_close(self):
        self.stop_event.set()  # Signal the worker thread to exit
        self.worker_thread.join()
        self.destroy()

# Run the GUI
if __name__ == "__main__":
    app = RemuxTool()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
