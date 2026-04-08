# Project Specification: jYT Music Desktop App

## 1. Project Overview
jYT Music is a Windows-native desktop application designed to provide a unified interface for streaming YouTube Music and playing local audio files. The app emphasizes speed, minimalist UI, and "always-available" control via global system hotkeys.

## 2. Core Features
- **Hybrid Source Toggle:** Switch between "Cloud Mode" (YouTube) and "Local Mode" (Local Directory).
- **YouTube Integration:** - Google OAuth2 login to access user playlists.
    - Search functionality for YouTube tracks/playlists.
    - **Backend:** Use `yt-dlp` to extract high-quality audio streams and `FFmpeg` for processing/playback.
- **Local Playback:** Indexing and playback of MP3, FLAC, and WAV files from a user-defined directory.
- **Global Hotkeys:** System-wide listeners for:
    - `Ctrl + Shift + Space`: Play / Pause
    - `Ctrl + Shift + Right`: Next Track
    - `Ctrl + Shift + Left`: Previous Track
- **Persistent Settings:** Save user preferences, API tokens (encrypted), and local paths.

## 3. Technical Architecture & Stack
- **IDE Environment:** Google Antigravity (Agent-centric workflow).
- **Language/Framework:** Python 3.11+ with **PySide6** (Qt) for the GUI.
- **Audio Engine:** `python-vlc` or `PyQt6.QtMultimedia` for cross-format support.
- **YouTube Core:** `yt-dlp` (Stream extraction) + `google-api-python-client` (Data API v3).
- **Global Hooks:** `pynput` or `system_hotkey` library.

## 4. Proposed Directory Structure
jYTMusic/
├── docs/
│   └── project_spec.md       # This file (Source of Truth)
├── src/
│   ├── main.py               # Entry point & App Loop
│   ├── audio_engine.py       # Logic for VLC/Local/YouTube playback
│   ├── shortcut_manager.py   # Global hotkey listener service
│   ├── yt_handler.py         # yt-dlp and YouTube API integration
│   ├── ui/
│   │   ├── main_window.ui    # Qt Designer file
│   │   └── style.qss         # Modern Dark Theme CSS
│   └── utils/
│       ├── config.py         # App settings & .env loading
│       └── auth.py           # Google OAuth2 Flow
├── tests/                    # Unit tests for audio and API
├── .env                      # API Keys (Excluded from Git)
└── requirements.txt          # Dependency list

## 5. UI/UX Architecture (Reference: User Mock-up)
The interface is divided into a Sidebar (Playlists), a Main View (Track Listing), and a Bottom Playback Bar.

### 5.1 Bottom Playback Bar (Left to Right)
* **Media Controls:** * **Previous/Back:** Logic: If song duration < 5% or < 5s, skip to previous ID. Otherwise, restart current song. Maintain a history buffer of 100 IDs.
    * **Play/Pause:** State-aware toggle.
    * **Next:** Skip to next ID in queue.
* **Timer:** Displaying `<present_time> / <total_duration>` (MM:SS). Refresh rate: ~250ms.
* **Center Info Block:**
    * Thumbnail (Left), Title (Bold, Top), Artist/Channel (Bottom).
    * **Like/Dislike:** Sync with YouTube API. Fetch status on song start. Dislike skips to next.
    * **Ellipsis (...) Menu:** Options for Start Mix, Download (Local caching), Save to/Remove from Playlist, and Share (URL copy).
* **Right Controls:**
    * **Volume:** Slider with integer percentage tooltip (0-100).
    * **Repeat Toggle:** 3-state (Off, Repeat All, Repeat One).
    * **Shuffle:** Toggle for randomized queue order.

### 5.2 Sidebar & Navigation
* **Playlist List:** Single-click navigation. Shows Playlist Title (Bold) and Creator.
* **Playlist Detail View:** Large header image (first track), creator name, track count, and total duration.
* **Track Interaction:** Single-click to play. Display duration for each track in the list.

### 5.3 User Integration
* Top-Right: User Icon with dropdown for Logout, Settings, and Downloads.

## 6. Technical Logic Improvements
* **API Consistency:** Ensure `yt-dlp` and YouTube Data API are fetching full playlist metadata (handling pagination if playlists > 50 tracks).
* **Downloading:** Implement local storage logic to prefer local files over streaming if a track has been downloaded via the "Download" menu option.
* **Single-Click Logic:** Shift from standard QListView double-click to `clicked` signal for faster navigation.

## 7. Development Phases (Agent Instructions)
- Phase 1: Foundation & UI: Scaffold the directory, set up a basic PySide6 window, and implement the "Cloud/Local" toggle switch.
- Phase 2: Global Shortcuts: Implement the background listener for hotkeys using pynput and verify it works even when the window is minimized.
- Phase 3: Local Engine: Build the local file scanner and basic playback logic for MP3/FLAC files.
- Phase 4: YouTube Integration: Implement yt-dlp stream extraction and basic search functionality.
- Phase 5: OAuth & Playlists: Add the Google Login flow to fetch user-specific playlists and finalize the UI/UX.