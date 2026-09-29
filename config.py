import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Directory configuration
BASE_DIR = Path(__file__).resolve().parent

# Di Vercel / Linux Cloud, direktori writable hanya ada di /tmp
if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    TEMP_DIR = Path("/tmp/tiktok_bypass")
else:
    TEMP_DIR = BASE_DIR / "temp"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

# File size limit in Megabytes (Telegram Standard Bot API download limit is 20 MB)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Batas waktu maksimal file sementara tersimpan (dalam detik, default 1 jam / 3600 detik)
# Agar penyimpanan tidak pernah penuh dan file lama otomatis terhapus
MAX_FILE_AGE_SECONDS = int(os.getenv("MAX_FILE_AGE_SECONDS", str(3600)))  # 1 jam


def clean_old_temp_files(max_age_seconds: int = MAX_FILE_AGE_SECONDS) -> int:
    """
    Menghapus file sementara di folder temp yang lebih tua dari batas waktu (otomatis pembersihan).
    Mengembalikan jumlah file yang berhasil dihapus.
    """
    import time
    deleted_count = 0
    now = time.time()
    if not TEMP_DIR.exists():
        return 0

    for item in TEMP_DIR.iterdir():
        if item.is_file():
            try:
                file_age = now - item.stat().st_mtime
                if file_age > max_age_seconds:
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
