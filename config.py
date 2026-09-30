import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8107353822:AAEh67cxdsjT1mXLowH8XP9q0gv-CU70GJE").strip()

# Directory configuration
BASE_DIR = Path(__file__).resolve().parent

import tempfile

# Di Render, Vercel, Railway, atau Linux Cloud, gunakan direktori temp cloud
if os.getenv("RENDER") or os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.name != "nt":
    TEMP_DIR = Path(tempfile.gettempdir()) / "tiktok_bypass"
else:
    TEMP_DIR = BASE_DIR / "temp"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

# File size limit in Megabytes (Telegram Standard Bot API download limit is 20 MB)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Batas retensi penyimpanan di Cloud (Maksimal 24 jam = 86400 detik)
# File sampah otomatis dibersihkan seketika dan maksimal sebelum 24 jam
MAX_RETENTION_HOURS = 24
MAX_FILE_AGE_SECONDS = int(os.getenv("MAX_FILE_AGE_SECONDS", str(MAX_RETENTION_HOURS * 3600)))


def get_storage_usage_mb() -> float:
    """Menghitung total ukuran file sementara yang tersimpan (dalam MB)."""
    total_bytes = 0
    dirs_to_check = [TEMP_DIR, BASE_DIR / "temp", Path(tempfile.gettempdir()) / "tiktok_bypass"]
    checked = set()

    for d in dirs_to_check:
        if d.exists() and d not in checked:
            checked.add(d)
            for item in d.iterdir():
                if item.is_file():
                    try:
                        total_bytes += item.stat().st_size
                    except Exception:
                        pass
    return total_bytes / (1024 * 1024)


def clean_old_temp_files(max_age_seconds: int = MAX_FILE_AGE_SECONDS) -> int:
    """
    Menghapus file sementara di cloud/lokal yang sudah berumur lebih dari batas waktu.
    Menjamin penyimpanan cloud tidak akan pernah penuh dan data otomatis terhapus dalam 24 jam.
    """
    import time
    deleted_count = 0
    now = time.time()
    dirs_to_clean = [TEMP_DIR, BASE_DIR / "temp", Path(tempfile.gettempdir()) / "tiktok_bypass"]
    cleaned_dirs = set()

    for target_dir in dirs_to_clean:
        if target_dir.exists() and target_dir not in cleaned_dirs:
            cleaned_dirs.add(target_dir)
            for item in target_dir.iterdir():
                if item.is_file():
                    try:
                        file_age = now - item.stat().st_mtime
                        # Hapus jika usia file melebihi batas waktu (atau jika max_age_seconds=0 untuk pembersihan total)
                        if file_age >= max_age_seconds:
                            item.unlink()
                            deleted_count += 1
                    except Exception:
                        pass
    return deleted_count


def get_ffmpeg_path() -> str:
    """Mendapatkan path executable FFmpeg dari imageio-ffmpeg atau sistem."""
    try:
        import imageio_ffmpeg

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and Path(ffmpeg_exe).exists():
            return ffmpeg_exe
    except Exception:
        pass

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    raise RuntimeError(
        "FFmpeg tidak ditemukan! Pastikan telah menginstal 'imageio-ffmpeg' atau FFmpeg di sistem."
    )
