import os
import subprocess
from yt_dlp import YoutubeDL

OUTPUT_DIR = "output_shorts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_youtube_clip(youtube_url: str, start_time: int = 0, duration: int = 30) -> str:
    """Downloads a segment of a YouTube video using robust fallback formats and renders vertical 9:16 short."""
    print(f"Downloading video from {youtube_url}...")
    
    ydl_opts = {
        'format': 'best[height<=720]/best',
        'outtmpl': os.path.join(OUTPUT_DIR, 'source_video.%(ext)s'),
        'socket_timeout': 30,
        'retries': 5
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as e:
        return f"Download Error: {str(e)}"
    
    output_clip = os.path.join(OUTPUT_DIR, f"clip_{int(start_time)}.mp4")
    
    # FFmpeg crop to 9:16 vertical format
    cmd = [
        "ffmpeg", "-y", "-ss", str(start_time), "-i", filename,
        "-t", str(duration), "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-c:a", "aac", output_clip
    ]
    
    print("Rendering vertical short clip...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode == 0:
        return f"Successfully generated clip: {output_clip}"
    else:
        return f"Error rendering clip: {result.stderr[-200:]}"
