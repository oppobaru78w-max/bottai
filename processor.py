import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import get_ffmpeg_path


def calculate_target_dims(w: int, h: int, quality_mode: str = "1080p") -> Tuple[int, int]:
    """
    Menghitung dimensi target video (1080p Full HD atau 4K Ultra HD)
    berdasarkan orientasi vertikal (9:16) atau horizontal (16:9).
    """
    w = w or 720
    h = h or 1280
    is_vertical = h >= w

    if quality_mode == "4k":
        # 4K Ultra HD
        tw, th = (2160, 3840) if is_vertical else (3840, 2160)
    elif quality_mode == "1080p":
        # Full HD (Standar Rekomendasi TikTok & Instagram Reels)
        tw, th = (1080, 1920) if is_vertical else (1920, 1080)
    else:
        # Original resolution (tetap dipastikan genap)
        tw, th = w, h

    tw = (int(tw) // 2) * 2
    th = (int(th) // 2) * 2
    return tw, th


PRESETS = {
    "standard": {
        "name": "💎 Full HD 1080p (Rekomendasi TikTok)",
        "desc": "Upscale otomatis ke 1080x1920 Full HD + Hapus C2PA + Lanczos Sharpening (Standar Resmi TikTok)",
        "quality_mode": "1080p",
        "get_vf": lambda tw, th: f"crop=trunc(iw*0.992/2)*2:trunc(ih*0.992/2)*2,scale={tw}:{th}:flags=lanczos,unsharp=5:5:0.4:3:3:0.0,noise=alls=2:allf=t+u,eq=contrast=1.01:saturation=1.01",
        "af": "atempo=1.005",
        "crf": "16",
        "speed_factor": 1.0,
    },
    "super_4k": {
        "name": "👑 Super 4K UHD (2160x3840 Ultra HD)",
        "desc": "Super Resolution 4K Ultra HD + Hapus C2PA + Lanczos Super-Sharp (Ketajaman Maksimal)",
        "quality_mode": "4k",
        "get_vf": lambda tw, th: f"crop=trunc(iw*0.992/2)*2:trunc(ih*0.992/2)*2,scale={tw}:{th}:flags=lanczos,unsharp=5:5:0.5:3:3:0.0,noise=alls=2:allf=t+u,eq=contrast=1.01:saturation=1.01",
        "af": "atempo=1.005",
        "crf": "16",
        "speed_factor": 1.0,
    },
    "pure_c2pa": {
        "name": "🛡️ Resolusi Asli (Hanya Hapus C2PA)",
        "desc": "Mempertahankan resolusi asli tanpa upscale + Hapus metadata C2PA",
        "quality_mode": "original",
        "get_vf": lambda tw, th: None,
        "af": None,
        "crf": "16",
        "speed_factor": 1.0,
    },
    "aggressive": {
        "name": "🔥 Agresif 1080p HD (Super Bypass)",
        "desc": "Full HD 1080p + Kecepatan 1.012x + ISO Grain Lebih Pekat (Untuk video membandel)",
        "quality_mode": "1080p",
        "get_vf": lambda tw, th: f"crop=trunc(iw*0.985/2)*2:trunc(ih*0.985/2)*2,scale={tw}:{th}:flags=lanczos,setpts=0.9881*PTS,noise=alls=4:allf=t+u,eq=contrast=1.02:saturation=1.02,unsharp=5:5:0.5:3:3:0.0",
        "af": "atempo=1.012",
        "crf": "17",
        "speed_factor": 1.012,
    },
    "cinematic": {
        "name": "🎬 Sinematik 1080p HD (35mm Grain)",
        "desc": "Full HD 1080p + Tekstur Film 35mm + Tone Hangat Estetik",
        "quality_mode": "1080p",
        "get_vf": lambda tw, th: f"crop=trunc(iw*0.992/2)*2:trunc(ih*0.992/2)*2,scale={tw}:{th}:flags=lanczos,noise=alls=3:allf=t+u,eq=contrast=1.02:saturation=1.03",
        "af": "atempo=1.005",
        "crf": "16",
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

    # Cek resolusi asli (misal: 720x1280, 1080x1920, 2160x3840)
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
    Memproses video: meng-upscale ke 1080p Full HD atau 4K Ultra HD dan menghilangkan jejak AI / C2PA.
    Mengembalikan (success, message, elapsed_time_seconds).
    """
    start_time = time.time()
    ffmpeg_exe = get_ffmpeg_path()

    if preset_key not in PRESETS:
        preset_key = "standard"

    preset = PRESETS[preset_key]
    info = get_video_info(input_path)

    # Hitung resolusi target (1080p atau 4K)
    quality_mode = preset.get("quality_mode", "1080p")
    target_w, target_h = calculate_target_dims(info["width"], info["height"], quality_mode)

    cmd = [ffmpeg_exe, "-y", "-hide_banner", "-i", input_path]

    # 1. Hapus metadata global, chapter, container tags, dan bitexact
    cmd.extend([
        "-map_metadata", "-1",
        "-map_chapters", "-1",
        "-fflags", "+bitexact",
        "-flags:v", "+bitexact",
        "-flags:a", "+bitexact",
    ])

    vf_filter = preset["get_vf"](target_w, target_h)

    if vf_filter:
        cmd.extend(["-vf", vf_filter])

    # Preset encoding kualitas ultra jernih (CRF 16 = Visually Lossless HD/4K)
    cmd.extend([
        "-c:v", "libx264",
        "-crf", preset["crf"],
        "-preset", "veryfast",
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
