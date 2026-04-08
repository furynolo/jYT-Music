import os

os.makedirs("assets", exist_ok=True)

icons = {
    "play": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="black"><path d="M8 5v14l11-7z"/></svg>',
    "pause": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="black"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>',
}

for name, svg in icons.items():
    with open(f"assets/{name}.svg", "w", encoding="utf-8") as f:
        f.write(svg)

print("Play/pause icons generated successfully.")
