# Building jYT Music Desktop

This document explains how to bundle the application into a standalone executable and create a Windows installer.

## Prerequisites

1. **Python 3.11+**
2. **Pip dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Inno Setup** (Required for the `.exe` installer wizard):
   - Download and install from [jrsoftware.org](https://jrsoftware.org/isinfo.php).

## Build Steps

### 1. Bundle with PyInstaller
Run the following command to create a standalone folder containing the executable and all assets:

```bash
pyinstaller jyt-music.spec
```

- Output will be located in `dist/jYT-Music-Desktop/`.
- You can run `dist/jYT-Music-Desktop/jYT-Music.exe` directly to verify the bundle.

### 2. Create the Installer Wizard
1. Open **Inno Setup Compiler**.
2. Open the `installer.iss` file located in the project root.
3. Click **Build > Compile** (or press `F9`).
4. The final installer (`jYT-Music-Setup.exe`) will be generated in the `installer_output/` folder.

## Troubleshooting

### Missing FFmpeg
If the app starts but cannot play music, ensure `ffmpeg.exe` and `ffprobe.exe` are present in `src/bin/` BEFORE running PyInstaller. The build script automatically detects and bundles them if they exist.

### SVG Icons
PyInstaller may not automatically set the `.exe` icon from an `.svg`. For a professional look, convert `src/assets/logo.svg` to `logo.ico` and update the `icon=` parameter in `jyt-music.spec`.
