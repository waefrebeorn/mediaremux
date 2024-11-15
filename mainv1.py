import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
import subprocess
import os
from tkinter import messagebox
import threading

# Check if ffmpeg is installed
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        messagebox.showerror("FFmpeg Not Found", "FFmpeg is required but not installed. Please install it and add to PATH.")
        return False

# Function to remux the video in a separate thread
def remux_video(file_path):
    if file_path.endswith((".mp4", ".mov", ".avi")):
        output_path = os.path.splitext(file_path)[0] + "_remuxed.mkv"
        command = ["ffmpeg", "-i", file_path, "-c", "copy", output_path]
        try:
            subprocess.run(command, check=True)
            messagebox.showinfo("Success", f"Remuxed file saved as:\n{output_path}")
        except subprocess.CalledProcessError:
            messagebox.showerror("Error", f"Failed to remux the file:\n{file_path}")
    else:
        messagebox.showerror("Invalid File", "Only MP4, MOV, and AVI files are supported.")

# Wrapper function to run remuxing in a thread
def remux_video_thread(file_path):
    thread = threading.Thread(target=remux_video, args=(file_path,))
    thread.start()

# Main GUI class
class RemuxTool(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Remux Tool for DaVinci Resolve")
        self.geometry("400x200")
        self.configure(bg="#2e2e2e")

        self.label = tk.Label(self, text="Drag and drop your video here", bg="#2e2e2e", fg="white", font=("Arial", 14))
        self.label.pack(pady=40)

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.on_drop)

        if not check_ffmpeg():
            self.quit()

    def on_drop(self, event):
        file_path = event.data.strip("{}")  # Clean up file path formatting
        remux_video_thread(file_path)  # Run remuxing in a separate thread

# Run the GUI
if __name__ == "__main__":
    app = RemuxTool()
    app.mainloop()
