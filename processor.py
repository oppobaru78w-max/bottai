import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import get_ffmpeg_path

PRESETS = {
    "standard": {
        "name": "⚡ Standar (Rekomendasi TikTok)",
        "desc": "Hapus C2PA + Micro Zoom 1% + Sensor Grain + Audio Pitch Shift (Keseimbangan visual terbaik)",
        "vf": "scale=trunc(iw*1.01/2)*2:trunc(ih*1.01/2)*2,crop=iw/1.01:ih/1.01,noise=alls=3:allf=t+u,eq=contrast=1.02:brightness=0.005:saturation=1.02,unsharp=3:3:0.35:3:3:0.0,fps=30",
        "af": "atempo=1.008,loudnorm=I=-16:TP=-1.5:LRA=11",
        "crf": "19",
        "speed_factor": 1.0,
    },
    "aggressive": {
        "name": "🔥 Agresif (Super Bypass)",
        "desc": "Semua filter Standar + Kecepatan 1.012x + ISO Grain Lebih Pekat (Untuk video membandel)",
        "vf": "scale=trunc(iw*1.02/2)*2:trunc(ih*1.02/2)*2,crop=iw/1.02:ih/1.02,setpts=0.9881*PTS,noise=alls=5:allf=t+u,eq=contrast=1.03:brightness=0.01:saturation=1.03,unsharp=5:5:0.5:5:5:0.0,fps=30",
        "af": "atempo=1.012,loudnorm=I=-16:TP=-1.5:LRA=11",
        "crf": "20",
        "speed_factor": 1.012,
    },
    "cinematic": {
        "name": "🎬 Sinematik (35mm Film Grain)",
        "desc": "Hapus C2PA + Tekstur Film 35mm + Warm Color Tone (Cocok untuk video estetika/storytelling)",
        "vf": "scale=trunc(iw*1.01/2)*2:trunc(ih*1.01/2)*2,crop=iw/1.01:ih/1.01,noise=alls=4:allf=t+u,eq=contrast=1.03:brightness=0.002:saturation=1.04,fps=30",
        "af": "atempo=1.005,loudnorm=I=-16:TP=-1.5:LRA=11",
        "crf": "19",
        "speed_factor": 1.0,
    },
    "metadata_only": {
        "name": "🛡️ Hanya Hapus C2PA Metadata",
        "desc": "Hapus 100% metadata C2PA/EXIF/XMP tanpa mengubah piksel video (Sangat cepat)",
        "vf": None,
        "af": None,
        "crf": "18",
        "speed_factor": 1.0,
    },
}


def get_video_info(file_path: str) -> Dict[str, Any]:
    """
    Menganalisis metadata video: durasi, resolusi, ada audio atau tidak.
    """
    ffmpeg_exe = get_ffmpeg_path()
    cmd = [ffmpeg_exe, "-hide_banner", "-i", file_path]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    stderr = res.stderr

    info = {
        "duration_sec": 0.0,
        "width": 0,
        "height": 0,
        "has_audio": False,
        "size_mb": os.path.getsize(file_path) / (1024 * 1024),
    }

    # Cek durasi (Duration: 00:01:23.45)
    dur_match = re.search(r"Duration:\s*(\d+):(\d+):([\d\.]+)", stderr)
    if dur_match:
        hours = float(dur_match.group(1))
        minutes = float(dur_match.group(2))
        seconds = float(dur_match.group(3))
        info["duration_sec"] = hours * 3600 + minutes * 60 + seconds

    # Cek resolusi (misal: 1080x1920 atau 720x1280)
    res_match = re.search(r"Video:.*?,.*?,\s*(\d{2,5})x(\d{2,5})", stderr)
    if res_match:
        info["width"] = int(res_match.group(1))
        info["height"] = int(res_match.group(2))

    # Cek audio
    if "Audio:" in stderr:
        info["has_audio"] = True

    return info


def process_video_sync(
    input_path: str,
    output_path: str,
    preset_key: str = "standard",
) -> Tuple[bool, str, float]:
    """
    Memproses video untuk menghilangkan jejak AI & C2PA.
    Mengembalikan (success, message, elapsed_time_seconds).
    """
    start_time = time.time()
    ffmpeg_exe = get_ffmpeg_path()

    if preset_key not in PRESETS:
        preset_key = "standard"

    preset = PRESETS[preset_key]
    info = get_video_info(input_path)

    cmd = [ffmpeg_exe, "-y", "-hide_banner", "-i", input_path]

    # 1. Hapus metadata global, chapter, dan bitexact
    cmd.extend([
        "-map_metadata", "-1",
        "-map_chapters", "-1",
        "-fflags", "+bitexact",
        "-flags:v", "+bitexact",
        "-flags:a", "+bitexact",
    ])

    if preset_key == "metadata_only":
        # Mode re-encode ringan untuk membersihkan container atoms
        cmd.extend([
            "-c:v", "libx264",
            "-crf", preset["crf"],
            "-preset", "faster",
            "-pix_fmt", "yuv420p",
        ])
        if info["has_audio"]:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-an"])
    else:
        # Terapkan Video Filter
        if preset.get("vf"):
            cmd.extend(["-vf", preset["vf"]])

        cmd.extend([
            "-c:v", "libx264",
            "-crf", preset["crf"],
            "-preset", "faster",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
        ])

        # Terapkan Audio Filter jika video memiliki audio
        if info["has_audio"] and preset.get("af"):
            cmd.extend([
                "-af", preset["af"],
                "-c:a", "aac",
                "-b:a", "192k",
            ])
        elif info["has_audio"]:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-an"])

    cmd.append(output_path)

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=300,  # 5 menit timeout
        )
        elapsed = time.time() - start_time

        if process.returncode != 0:
            error_msg = process.stderr[-400:] if process.stderr else "FFmpeg error"
            return False, f"Gagal memproses video: {error_msg}", elapsed

        if not Path(output_path).exists() or os.path.getsize(output_path) == 0:
            return False, "File output kosong atau tidak terbentuk.", elapsed

        return True, "Berhasil memproses video!", elapsed

    except subprocess.TimeoutExpired:
        return False, "Proses video timeout (melebihi batas 5 menit).", time.time() - start_time
    except Exception as e:
        return False, f"Terjadi kesalahan sistem: {str(e)}", time.time() - start_time
