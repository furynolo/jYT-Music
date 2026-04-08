# jYT Music

A Windows-native desktop application for streaming YouTube Music and playing local audio files. Built with Python and PySide6.

## Features
- **Categorized Search**: Filter by Songs, Albums, Artists, and more with high-quality metadata.
- **YouTube Integration**: Stream directly from YouTube Music using high-bitrate audio.
- **Local Playback**: Play your local MP3, FLAC, and WAV files seamlessly.
- **Global Shortcuts**: Control playback even when the app isn't focused.
- **Minimalist UI**: Modern dark-mode interface inspired by the official YouTube Music experience.

## Prerequisites
- **Python 3.11+**
- **FFmpeg**: The application requires FFmpeg for streaming and downloads. You have two options:
    1. **System PATH (Recommended)**: Install FFmpeg on your system and ensure it's available in your `PATH`.
    2. **Bundled**: Place `ffmpeg.exe` and `ffprobe.exe` directly into the `src/bin/` directory.

> [!NOTE]
> The `src/bin/` folder is listed in `.gitignore` to prevent large binaries from bloating the repository.


## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/jyt-music-desktop-app.git
   cd jyt-music-desktop-app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Google API Credentials**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project and enable the **YouTube Data API v3**.
   - Create **OAuth 2.0 Client IDs** (type: Desktop App).
   - Download the JSON credentials and save them as `docs/client_secret.json`. (See `docs/client_secret.json.example` for the format).

4. **Run the app**:
   ```bash
   python src/main.py
   ```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
