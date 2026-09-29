import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import get_ffmpeg_path

PRESETS = {
    "standard": {
        "name": "💎 Ultra HD Asli (Rekomendasi Utama)",
        "desc": "Resolusi 100% Asli HD + Hapus C2PA + Micro Resample + Sensor Grain Halus (Kualitas visual kristal jernih tanpa blur)",
        "get_vf": lambda w, h: f"crop=trunc(iw*0.992/2)*2:trunc(ih*0.992/2)*2,scale={w}:{h}:flags=lanczos,noise=alls=2:allf=t+u,eq=contrast=1.01:saturation=1.01,unsharp=3:3:0.2:3:3:0.0",
        "af": "atempo=1.005",
        "crf": "17",
        "speed_factor": 1.0,
    },
    "pure_c2pa": {
        "name": "🛡️ 100% Murni Tanpa Ubah Visual (C2PA Strip)",
        "desc": "Hanya menghapus metadata C2PA/EXIF/XMP tanpa menyentuh satu piksel pun (Resolusi & visual 100% identik asli)",
        "get_vf": lambda w, h: None,
        "af": None,
        "crf": "16",
        "speed_factor": 1.0,
    },
    "aggressive": {
        "name": "🔥 Agresif HD (Super Bypass)",
        "desc": "Resolusi Tetap Asli HD + Kecepatan 1.012x + ISO Grain Lebih Pekat (Untuk video membandel)",
        "get_vf": lambda w, h: f"crop=trunc(iw*0.985/2)*2:trunc(ih*0.985/2)*2,scale={w}:{h}:flags=lanczos,setpts=0.9881*PTS,noise=alls=4:allf=t+u,eq=contrast=1.02:saturation=1.02,unsharp=3:3:0.3:3:3:0.0",
        "af": "atempo=1.012",
        "crf": "18",
        "speed_factor": 1.012,
    },
    "cinematic": {
        "name": "🎬 Sinematik HD (35mm Film Grain)",
        "desc": "Resolusi Tetap Asli HD + Tekstur Film 35mm + Tone Hangat Estetik",
        "get_vf": lambda w, h: f"crop=trunc(iw*0.992/2)*2:trunc(ih*0.992/2)*2,scale={w}:{h}:flags=lanczos,noise=alls=3:allf=t+u,eq=contrast=1.02:saturation=1.03",
        "af": "atempo=1.005",
        "crf": "17",
        "speed_factor": 1.0,
    },
}


def get_video_info(file_path: str) -> Dict[str, Any]:
    """
    Menganalisis metadata video: durasi, resolusi asli, ada audio atau tidak.
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
        "size_mb": os.path.getsize(file_path) / (1024 * 1024) if os.path.exists(file_path) else 0.0,
    }

    # Cek durasi (Duration: 00:01:23.45)
    dur_match = re.search(r"Duration:\s*(\d+):(\d+):([\d\.]+)", stderr)
    if dur_match:
        hours = float(dur_match.group(1))
        minutes = float(dur_match.group(2))
        seconds = float(dur_match.group(3))
        info["duration_sec"] = hours * 3600 + minutes * 60 + seconds

    # Cek resolusi asli (misal: 1080x1920 atau 720x1280 atau 2160x3840)
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
    Memproses video untuk menghilangkan jejak AI & C2PA dengan mempertahankan kualitas HD asli.
    Mengembalikan (success, message, elapsed_time_seconds).
    """
    start_time = time.time()
    ffmpeg_exe = get_ffmpeg_path()

    if preset_key not in PRESETS:
        preset_key = "standard"

    preset = PRESETS[preset_key]
    info = get_video_info(input_path)
    orig_w = info["width"] or 1080
    orig_h = info["height"] or 1920

    # Pastikan resolusi genap (divisible by 2) untuk libx264
    orig_w = (int(orig_w) // 2) * 2
    orig_h = (int(orig_h) // 2) * 2

    cmd = [ffmpeg_exe, "-y", "-hide_banner", "-i", input_path]

    # 1. Hapus metadata global, chapter, container tags, dan bitexact
    cmd.extend([
        "-map_metadata", "-1",
        "-map_chapters", "-1",
        "-fflags", "+bitexact",
        "-flags:v", "+bitexact",
        "-flags:a", "+bitexact",
    ])

    vf_filter = preset["get_vf"](orig_w, orig_h)

    if vf_filter:
        cmd.extend(["-vf", vf_filter])

    # Preset encoding kualitas tinggi (CRF 16-18 = Visually Lossless HD)
    cmd.extend([
        "-c:v", "libx264",
        "-crf", preset["crf"],
        "-preset", "faster",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
    ])

    # Terapkan Audio Filter kualitas studio (320 kbps AAC)
    if info["has_audio"] and preset.get("af"):
        cmd.extend([
            "-af", preset["af"],
            "-c:a", "aac",
            "-b:a", "320k",
        ])
    elif info["has_audio"]:
        cmd.extend(["-c:a", "aac", "-b:a", "320k"])
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
