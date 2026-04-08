import os

class LocalScanner:
    SUPPORTED_EXTENSIONS = {'.mp3', '.flac', '.wav', '.m4a'}

    @classmethod
    def scan_directory(cls, directory_path):
        """
        Recursively scans the directory for supported audio files.
        Returns a list of dictionaries containing file info.
        """
        audio_files = []
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            return audio_files

        for root, _, files in os.walk(directory_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in cls.SUPPORTED_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    audio_files.append({
                        "name": file,
                        "path": file_path,
                        "extension": ext
                    })
        
        # Sort alphabetically by name
        audio_files.sort(key=lambda x: x["name"].lower())
        return audio_files
