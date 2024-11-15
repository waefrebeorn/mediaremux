# Video Remux Tool for DaVinci Resolve

This Python-based tool provides a GUI interface that allows users to drag and drop multiple video files for remuxing into DaVinci Resolve-compatible MKV containers. It’s designed to handle large volumes of video files efficiently, making it ideal for overnight batch processing.

## Key Features

- **Drag-and-Drop GUI**: Easily drag and drop video files for seamless queuing.
- **Supported Formats**: Works with MP4, MOV, and AVI files, remuxing them into MKV containers.
- **Fast Processing**: The tool copies video and audio streams directly without re-encoding, ensuring fast, high-quality conversions.
- **Continuous Queueing**: Users can add files to the queue at any time, allowing background processing while browsing or during an overnight session.

## Prerequisites

1. **Python 3.7 or higher**: Ensure Python is installed and accessible from your system PATH.
2. **FFmpeg**: This tool requires FFmpeg, which must be installed and added to the system PATH.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies**:
   ```bash
   pip install tkinterdnd2
   ```

## Usage

1. **Run the Tool**:
   ```bash
   python main.py
   ```

2. **Using the Drag-and-Drop Interface**:
   - Drag video files (MP4, MOV, AVI) into the application window. Each file will be queued and processed in the background.
   - The tool displays real-time status updates in the queue, including:
     - `Queued`: File is waiting to be processed.
     - `Completed`: File has been successfully remuxed to MKV.
     - `Error`: An error occurred during remuxing.
     - `Invalid File`: Unsupported file format.

3. **Continuous Processing**:
   - The tool allows continuous addition of files. You can add new files even while others are processing, making it suitable for unattended overnight processing of large volumes.

4. **Exiting the Tool**:
   - When you close the window, the program will gracefully stop processing, ensuring all running tasks are completed.

## Script Overview

### Code Structure

- **File Queueing**: Dragged files are added to a queue (`remux_queue`) for processing.
- **Background Processing**: The script uses multithreading to handle each file in the queue, keeping the GUI responsive.
- **Queue Status Display**: A `Listbox` displays the status of each file in the queue.

### Remuxing Process

The tool leverages FFmpeg to remux files by copying the audio and video streams directly into an MKV container without re-encoding, preserving the original quality. This process is particularly fast and lightweight, as only the container format changes.

## Requirements

- **FFmpeg**: [Download FFmpeg](https://ffmpeg.org/download.html) and add it to your system PATH.

## Example Workflow

1. **Start the Tool**: Open the tool and begin dropping files.
2. **Monitor the Queue**: Watch the list update as files are queued, processed, and completed.
3. **Add More Files**: Continue adding files as needed; the tool will process them in sequence.
4. **Check Results**: Completed files are saved in the same location as the original, with `_remuxed.mkv` appended to the filename.

## Notes

- **Compatibility**: This tool is optimized for DaVinci Resolve and should improve compatibility by converting MP4, MOV, and AVI files to MKV format.
- **Batch Processing**: Ideal for users with extensive video libraries, as it handles large volumes efficiently.

## Troubleshooting

- **FFmpeg Not Found**: If FFmpeg is not installed or added to the system PATH, the tool will prompt you to install it.
- **Invalid Files**: Only MP4, MOV, and AVI files are supported. Unsupported files will display an "Invalid File" message.

## License

This project is open-source and licensed under the MIT License.

---

By following these instructions, users can easily install, run, and benefit from the Video Remux Tool for DaVinci Resolve.
