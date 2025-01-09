# Video Transcoder - HEVC Game Stream Optimizer

A Python-based GUI application that provides GPU-accelerated video transcoding optimized for game capture and streaming using NVIDIA's NVENC encoder. This tool is specifically designed for high-quality, efficient compression of gameplay footage with a user-friendly interface.

## Key Features

- **GPU-Accelerated HEVC/H.265 Encoding**: Uses NVIDIA's NVENC for fast, high-quality compression
- **Game Stream Optimized Settings**: Tuned for high motion content with quality-focused parameters
- **Drag-and-Drop Interface**: Simple GUI for queuing multiple video files
- **Multi-File Processing**: Queue and process multiple videos sequentially
- **Progress Tracking**: Real-time progress updates and status monitoring
- **Flexible Output Options**: Custom output directory selection and optional 1080p downscaling
- **Automatic Codec Detection**: Falls back to H.264 if HEVC is not supported

## Prerequisites

1. **NVIDIA GPU**: Required for NVENC hardware acceleration
2. **Python 3.x**
3. **FFmpeg**: Must be installed and accessible in your system PATH
4. **Required Python Packages**:
   ```bash
   pip install tkinterdnd2
   ```

## Encoding Specifications

### Video Settings
- **Codec**: HEVC (H.265) with NVENC hardware acceleration
- **Preset**: p2 (Fast)
- **Tuning**: High Quality
- **Bitrate Control**: Variable Bitrate (VBR)
- **Target Bitrate**: 20 Mbps
- **Maximum Bitrate**: 30 Mbps
- **Buffer Size**: 40 Mbps
- **Quality Features**:
  - Spatial AQ (Adaptive Quantization)
  - Temporal AQ
  - 3 Reference Frames
  - 250-frame GOP Size
  - 3 B-Frames

### Audio Settings
- **Codec**: AAC
- **Bitrate**: 192 kbps
- **Sample Rate**: 48 kHz
- **Smart Stream Copy**: Preserves original AAC streams when possible

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg**:
   - Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Add FFmpeg to your system PATH

## Usage

1. **Launch the Application**:
   ```bash
   python main.py
   ```

2. **Using the Interface**:
   - **Add Files**: Either drag and drop video files into the window or use the "Browse Files" button
   - **Select Output Location** (Optional): Choose a custom output folder
   - **Downscaling Option**: Toggle "Force scale to 1080p" if needed
   - **Start Processing**: Click "Start Transcoding"
   - **Monitor Progress**: Watch the progress bar and status updates
   - **Cancel Operations**: Use "Stop Transcoding" to halt current operations
   - **Clear Queue**: Remove all queued items with "Clear Queue"

## Output Specifications

- Files are saved with "_transcoded" suffix in MP4 format
- Maintains original metadata and stream mapping
- FastStart flag enabled for optimized streaming
- Maintains original resolution unless 1080p downscaling is enabled
- Preserves frame rate and color space

## Performance

- Hardware acceleration for both decoding (when available) and encoding
- Typically achieves 3-4x faster than real-time processing
- Optimized thread queue handling for improved stability
- Memory-efficient processing suitable for long recordings

## Error Handling

- Automatic codec support detection
- Resolution checking with warnings for sub-HD content
- Comprehensive error reporting in the GUI
- Graceful process termination
- Failed operation notifications

## Known Limitations

- Requires NVIDIA GPU for hardware acceleration
- HEVC support depends on GPU capabilities
- Limited to FFmpeg supported input formats

## Troubleshooting

### Common Issues

1. **FFmpeg Not Found**:
   - Ensure FFmpeg is properly installed
   - Verify FFmpeg is in system PATH
   - Restart application after FFmpeg installation

2. **NVENC Errors**:
   - Update NVIDIA drivers
   - Verify GPU supports NVENC
   - Check if other applications are using NVENC

3. **Performance Issues**:
   - Close other GPU-intensive applications
   - Monitor GPU temperature
   - Consider reducing maximum concurrent processes

## System Requirements

- Windows/Linux/macOS with Python 3.x support
- NVIDIA GPU with NVENC support
- Sufficient storage space for output files
- 8GB RAM recommended
- FFmpeg installed and in system PATH

## Development

This project is open for contributions. Key areas for potential improvement:

- Additional output format options
- Custom encoding profiles
- Advanced audio options
- Batch profile application
- GPU load balancing

## License

This project is open-source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

---

For bug reports or feature requests, please use the issue tracker.