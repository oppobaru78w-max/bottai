import os
import sys
import uuid
import logging
import asyncio
from pathlib import Path

# Memastikan output terminal Windows mendukung karakter UTF-8 / emoji
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

import config
from processor import (
    PRESETS,
    get_video_info,
    process_video_sync,
)

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# User preference storage (in-memory: user_id -> default_preset)
user_preferences = {}

# Active jobs tracking (to prevent spam/race conditions)
active_jobs = set()


def get_user_preset(user_id: int) -> str:
    return user_preferences.get(user_id, "ask")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk perintah /start"""
    user_name = update.effective_user.first_name if update.effective_user else "Pengguna"
    welcome_text = (
        f"👋 **Halo {user_name}! Selamat datang di TikTok AI Bypass Bot.**\n\n"
        "Bot ini dirancang khusus untuk memodifikasi video hasil buatan AI "
        "(Sora, Kling, Runway, Midjourney, CapCut AI, Haiper, dsb.) agar **lolos deteksi algoritma AI TikTok** "
        "dan tidak otomatis diberi label *'AI-generated content'*.\n\n"
        "✨ **Bagaimana Bot Ini Bekerja?**\n"
        "1. 🛡️ **Pembersihan C2PA**: Menghapus 100% metadata tersembunyi (Content Credentials, EXIF, XMP, UUID).\n"
        "2. 🔬 **Resampling Grid Piksel**: Melakukan micro-crop & zoom 1% untuk mengacak pola matematis model difusi AI.\n"
        "3. 📸 **Simulasi Sensor Kamera**: Menambahkan natural optical ISO grain untuk menghilangkan kehalusan artifisial AI.\n"
        "4. 🎵 **Audio Frequency Shifting**: Menggeser mikro tempo & frekuensi suara untuk melewati detektor suara AI.\n\n"
        "🚀 **Cara Pakai:**\n"
        "Cukup **kirimkan video** Anda ke chat ini (maksimal 20 MB)!\n\n"
        "Perintah berguna:\n"
        "• /tips - Tips penting agar video lolos & FYP di TikTok\n"
        "• /mode - Pilih preset default pemrosesan\n"
        "• /help - Bantuan & penjelasan fitur"
    )

    keyboard = [
        [
            InlineKeyboardButton("💡 Tips Upload TikTok", callback_data="show_tips"),
            InlineKeyboardButton("⚙️ Pilih Mode Default", callback_data="show_modes"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk perintah /help"""
    help_text = (
        "📖 **Panduan & Penjelasan Bot Anti-Deteksi AI**\n\n"
        "TikTok menggunakan sistem otomatis berlapis untuk mendeteksi video AI:\n"
        "• **Deteksi Metadata**: Memeriksa tag C2PA dari platform generator AI.\n"
        "• **Deteksi Pola Visual**: Menganalisis frekuensi Fourier dan piksel yang terlalu mulus tanpa noise lensa kamera.\n"
        "• **Deteksi Spektral Audio**: Mengenali pola frekuensi suara sintetis (seperti ElevenLabs).\n\n"
        "⚙️ **Pilihan Preset Pemrosesan:**\n\n"
        "1. **⚡ Standar (Rekomendasi)**\n"
        "   Hapus C2PA + Micro Zoom 1% + Sensor Grain Halus + Micro Audio Pitch. Sangat seimbang & mempertahankan kualitas HD.\n\n"
        "2. **🔥 Agresif (Super Bypass)**\n"
        "   Filter Standar + Pergeseran Kecepatan 1.012x + ISO Grain Lebih Pekat. Direkomendasikan untuk video yang membandel tetap terdeteksi AI.\n\n"
        "3. **🎬 Sinematik (35mm Grain)**\n"
        "   Menambahkan tekstur grain film 35mm dan penyesuaian warna hangat yang estetis.\n\n"
        "4. **🛡️ Hanya C2PA Metadata**\n"
        "   Hanya menghapus metadata container tanpa mengubah piksel visual (proses kilat 1-2 detik).\n\n"
        "💡 *Kirimkan video Anda sekarang untuk memulai!*"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def tips_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk perintah /tips"""
    tips_text = (
        "💡 **5 Tips Ampuh Lolos Deteksi AI & Tembus FYP TikTok:**\n\n"
        "1. **Gunakan Audio Tren TikTok** 🎵\n"
        "   Saat mengunggah ke TikTok, pilih lagu/suara yang sedang tren dari perpustakaan TikTok. Jika video Anda sudah ada voiceover, atur volume lagu tren ke **1% - 3%** agar algoritma TikTok membaca video menggunakan audio resmi aplikasi.\n\n"
        "2. **Jangan Centang Opsi AI** ❌\n"
        "   Pada halaman posting akhir TikTok (sebelum tombol Kirim), pastikan opsi *'AI-generated content / Konten yang dibuat AI'* dalam posisi **MATI (OFF)**.\n\n"
        "3. **Tambahkan Elemen Native TikTok** ✍️\n"
        "   Tambahkan sedikit teks atau stiker bawaan editor TikTok di layar (misal judul atau pertanyaan pancingan). TikTok sangat memprioritaskan video yang menggunakan fitur bawaannya.\n\n"
        "4. **Jangan Upload Beruntun** ⏱️\n"
        "   Beri jeda minimal 1-2 jam antar postingan agar akun Anda tidak ditandai sebagai bot otomatis.\n\n"
        "5. **Gunakan Caption & Hashtag Alami** 🏷️\n"
        "   Gunakan hashtag niche spesifik dan buat kalimat caption yang memicu interaksi penonton di kolom komentar."
    )
    await update.message.reply_text(tips_text, parse_mode=ParseMode.MARKDOWN)


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk memilih mode default"""
    user_id = update.effective_user.id
    current_mode = user_preferences.get(user_id, "ask")

    text = (
        "⚙️ **Pengaturan Mode Pemrosesan (Ultra HD):**\n\n"
        f"Mode saat ini: `{current_mode.upper()}`\n\n"
        "Pilih bagaimana Anda ingin bot memproses setiap video yang dikirim:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "💎 Ultra HD Asli (Rekomendasi)" + (" ✅" if current_mode == "standard" else ""),
                callback_data="set_pref_standard",
            )
        ],
        [
            InlineKeyboardButton(
                "🛡️ 100% Murni (C2PA Strip)" + (" ✅" if current_mode == "pure_c2pa" else ""),
                callback_data="set_pref_pure_c2pa",
            )
        ],
        [
            InlineKeyboardButton(
                "🔥 Agresif HD (Super Bypass)" + (" ✅" if current_mode == "aggressive" else ""),
                callback_data="set_pref_aggressive",
            )
        ],
        [
            InlineKeyboardButton(
                "🎬 Sinematik HD (35mm Grain)" + (" ✅" if current_mode == "cinematic" else ""),
                callback_data="set_pref_cinematic",
            )
        ],
        [
            InlineKeyboardButton(
                "❓ Selalu Tanya Setiap Kirim Video" + (" ✅" if current_mode == "ask" else ""),
                callback_data="set_pref_ask",
            )
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def handle_video_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler saat menerima pesan berisi Video atau Dokumen Video"""
    message = update.message
    user_id = update.effective_user.id

    if user_id in active_jobs:
        await message.reply_text(
            "⏳ Anda masih memiliki antrean video yang sedang diproses. Mohon tunggu hingga selesai ya!"
        )
        return

    # Ambil file telegram
    video_obj = message.video
    if not video_obj and message.document:
        doc = message.document
        if doc.mime_type and doc.mime_type.startswith("video/"):
            video_obj = doc
        elif doc.file_name and doc.file_name.lower().endswith((".mp4", ".mov", ".mkv", ".webm", ".avi")):
            video_obj = doc

    if not video_obj:
        await message.reply_text(
            "⚠️ Format file tidak didukung. Mohon kirimkan video dalam format MP4, MOV, atau MKV."
        )
        return

    # Cek batas ukuran file (Telegram standard API max 20MB)
    file_size_mb = (video_obj.file_size or 0) / (1024 * 1024)
    if file_size_mb > config.MAX_FILE_SIZE_MB:
        await message.reply_text(
            f"❌ **Ukuran video terlalu besar ({file_size_mb:.1f} MB)!**\n\n"
            f"Telegram membatasi bot mengunduh file maksimal **{config.MAX_FILE_SIZE_MB} MB**.\n"
            "💡 *Tips: Anda bisa memotong durasi video atau mengompres sedikit resolusinya sebelum dikirimkan ke bot.*",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Simpan info file di context.user_data untuk diproses
    file_id = video_obj.file_id
    user_preset = get_user_preset(user_id)

    # Simpan session job
    job_id = str(uuid.uuid4())[:8]
    context.user_data[f"job_{job_id}"] = {
        "file_id": file_id,
        "file_size_mb": file_size_mb,
        "duration": getattr(video_obj, "duration", 0),
        "width": getattr(video_obj, "width", 0),
        "height": getattr(video_obj, "height", 0),
    }

    # Jika user telah mengatur preset otomatis (bukan 'ask')
    if user_preset != "ask":
        await run_process_pipeline(update, context, job_id, user_preset)
        return

    # Jika 'ask', tampilkan pilihan preset
    caption = (
        f"📹 **Video Diterima!**\n"
        f"• Ukuran: `{file_size_mb:.2f} MB`\n"
        f"• Resolusi Asli: `{video_obj.width}x{video_obj.height}` (HD Dijaga Penuh)\n\n"
        f"🎯 **Pilih Mode Bypass Deteksi AI TikTok (Kualitas HD Asli):**"
    )

    keyboard = [
        [
            InlineKeyboardButton("💎 Ultra HD Asli (Rekomendasi Utama)", callback_data=f"proc_{job_id}_standard"),
        ],
        [
            InlineKeyboardButton("🛡️ 100% Murni (Hanya Hapus C2PA)", callback_data=f"proc_{job_id}_pure_c2pa"),
        ],
        [
            InlineKeyboardButton("🔥 Agresif HD (Super Bypass)", callback_data=f"proc_{job_id}_aggressive"),
        ],
        [
            InlineKeyboardButton("🎬 Sinematik HD (35mm Grain)", callback_data=f"proc_{job_id}_cinematic"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def run_process_pipeline(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    job_id: str,
    preset_key: str,
    status_message=None,
) -> None:
    """Menjalankan proses pengunduhan, pemrosesan FFmpeg, dan pengunggahan kembali."""
    user_id = update.effective_user.id
    job_data = context.user_data.get(f"job_{job_id}")

    if not job_data:
        err_text = "❌ Sesi video telah kedaluwarsa. Silakan kirimkan video Anda kembali."
        if status_message:
            await status_message.edit_text(err_text)
        else:
            await update.effective_chat.send_message(err_text)
        return

    active_jobs.add(user_id)
    preset_info = PRESETS.get(preset_key, PRESETS["standard"])

    # Path berkas sementara
    session_uid = f"{user_id}_{job_id}_{int(asyncio.get_event_loop().time())}"
    input_file = config.TEMP_DIR / f"input_{session_uid}.mp4"
    output_file = config.TEMP_DIR / f"output_{session_uid}.mp4"

    try:
        # Step 1: Status Unduh
        status_text = f"📥 **Mengunduh video dari Telegram...**\n`Preset: {preset_info['name']}`"
        if status_message:
            await status_message.edit_text(status_text, parse_mode=ParseMode.MARKDOWN)
        else:
            status_message = await update.effective_chat.send_message(
                status_text, parse_mode=ParseMode.MARKDOWN
            )

        await update.effective_chat.send_action(ChatAction.RECORD_VIDEO)

        # Download file
        tg_file = await context.bot.get_file(job_data["file_id"])
        await tg_file.download_to_drive(custom_path=input_file)

        # Step 2: Proses Bypass
        await status_message.edit_text(
            f"⚙️ **Menghilangkan Jejak AI & C2PA...**\n"
            f"• Mode: `{preset_info['name']}`\n"
            f"• Proses: Menghapus C2PA, meresample piksel, menyisipkan noise optik...",
            parse_mode=ParseMode.MARKDOWN,
        )
        await update.effective_chat.send_action(ChatAction.RECORD_VIDEO)

        # Jalankan FFmpeg secara async di threadpool agar tidak memblokir bot
        success, msg, elapsed = await asyncio.to_thread(
            process_video_sync,
            str(input_file),
            str(output_file),
            preset_key,
        )

        if not success:
            await status_message.edit_text(
                f"❌ **Pemrosesan Gagal!**\n\nDetail: `{msg}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Step 3: Unggah Video Hasil
        await status_message.edit_text(
            f"📤 **Mengunggah video hasil bypass ({elapsed:.1f} detik)...**",
            parse_mode=ParseMode.MARKDOWN,
        )
        await update.effective_chat.send_action(ChatAction.UPLOAD_VIDEO)

        processed_info = get_video_info(str(output_file))

        caption = (
            f"✅ **Video Berhasil Diproses! (Lolos Deteksi AI)**\n\n"
            f"🎯 **Mode**: `{preset_info['name']}`\n"
            f"⏱️ **Waktu Proses**: `{elapsed:.1f} detik`\n"
            f"📏 **Resolusi**: `{processed_info['width']}x{processed_info['height']}`\n"
            f"📦 **Ukuran**: `{processed_info['size_mb']:.2f} MB`\n\n"
            f"🛡️ **Status Keamanan TikTok:**\n"
            f"• C2PA Metadata: 100% Dihapus ✅\n"
            f"• Latent AI Grid: Diacak (Resampled) ✅\n"
            f"• Sensor Grain: Ditambahkan ✅\n"
            f"• Voice Pitch: Diselaraskan ✅\n\n"
            f"💡 *Tips: Gunakan audio tren TikTok saat upload & matikan opsi 'AI-generated content'. Ketik /tips untuk panduan lengkap.*"
        )

        with open(output_file, "rb") as video_fp:
            await update.effective_chat.send_video(
                video=video_fp,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True,
                width=processed_info["width"],
                height=processed_info["height"],
            )

        # Hapus pesan status sementara
        try:
            await status_message.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Error during video processing: {e}", exc_info=True)
        if status_message:
            await status_message.edit_text(
                f"❌ **Terjadi kesalahan tak terduga:**\n`{str(e)}`",
                parse_mode=ParseMode.MARKDOWN,
            )
    finally:
        # Bersihkan memori pekerjaan & berkas sementara
        active_jobs.discard(user_id)
        context.user_data.pop(f"job_{job_id}", None)

        if input_file.exists():
            try:
                input_file.unlink()
            except Exception:
                pass
        if output_file.exists():
            try:
                output_file.unlink()
            except Exception:
                pass


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler interaksi tombol inline keyboard"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "show_tips":
        tips_text = (
            "💡 **5 Tips Ampuh Lolos Deteksi AI & Tembus FYP TikTok:**\n\n"
            "1. **Gunakan Audio Tren TikTok** 🎵\n"
            "   Saat upload, gunakan musik dari library TikTok. Atur volumenya ke 1-3% jika ingin tetap memakai suara video asli.\n\n"
            "2. **Jangan Centang Opsi AI** ❌\n"
            "   Pastikan opsi 'Konten yang dibuat AI' dalam posisi OFF.\n\n"
            "3. **Tambahkan Elemen Native TikTok** ✍️\n"
            "   Gunakan stiker atau teks bawaan TikTok.\n\n"
            "4. **Jangan Upload Beruntun** ⏱️\n"
            "   Beri jeda minimal 1-2 jam antar postingan.\n\n"
            "5. **Gunakan Caption & Hashtag Alami** 🏷️"
        )
        await query.message.reply_text(tips_text, parse_mode=ParseMode.MARKDOWN)

    elif data == "show_modes":
        user_id = query.from_user.id
        current_mode = user_preferences.get(user_id, "ask")
        keyboard = [
            [
                InlineKeyboardButton(
                    "💎 Ultra HD Asli (Rekomendasi)" + (" ✅" if current_mode == "standard" else ""),
                    callback_data="set_pref_standard",
                )
            ],
            [
                InlineKeyboardButton(
                    "🛡️ 100% Murni (C2PA Strip)" + (" ✅" if current_mode == "pure_c2pa" else ""),
                    callback_data="set_pref_pure_c2pa",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔥 Agresif HD (Super Bypass)" + (" ✅" if current_mode == "aggressive" else ""),
                    callback_data="set_pref_aggressive",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎬 Sinematik HD (35mm Grain)" + (" ✅" if current_mode == "cinematic" else ""),
                    callback_data="set_pref_cinematic",
                )
            ],
            [
                InlineKeyboardButton(
                    "❓ Selalu Tanya Setiap Kirim Video" + (" ✅" if current_mode == "ask" else ""),
                    callback_data="set_pref_ask",
                )
            ],
        ]
        await query.message.reply_text(
            "⚙️ **Pilih Mode Default Pemrosesan (Ultra HD):**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("set_pref_"):
        new_pref = data.replace("set_pref_", "")
        user_id = query.from_user.id
        user_preferences[user_id] = new_pref
        pref_names = {
            "standard": "💎 Ultra HD Asli (Rekomendasi Utama)",
            "pure_c2pa": "🛡️ 100% Murni (C2PA Strip)",
            "aggressive": "🔥 Agresif HD (Super Bypass)",
            "cinematic": "🎬 Sinematik HD (35mm Grain)",
            "ask": "❓ Selalu Tanya Setiap Kirim Video",
        }
        await query.edit_message_text(
            f"✅ **Mode Default Berhasil Disimpan!**\n\n"
            f"Pilihan Anda sekarang: **{pref_names.get(new_pref, new_pref)}**.\n"
            "Setiap video yang Anda kirim akan langsung diproses dengan mode ini.",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data.startswith("proc_"):
        # Format: proc_{job_id}_{preset}
        parts = data.split("_")
        if len(parts) >= 3:
            job_id = parts[1]
            preset_key = "_".join(parts[2:])
            await run_process_pipeline(
                update=update,
                context=context,
                job_id=job_id,
                preset_key=preset_key,
                status_message=query.message,
            )


async def periodic_temp_cleanup() -> None:
    """Task latar belakang untuk membersihkan file sementara secara berkala (setiap 30 menit)."""
    while True:
        try:
            await asyncio.sleep(1800)  # Cek setiap 30 menit
            deleted = config.clean_old_temp_files()
            if deleted > 0:
                logger.info(f"🧹 Auto-Cleanup: Berhasil menghapus {deleted} file sementara lama.")
        except Exception as e:
            logger.warning(f"Gagal menjalankan auto-cleanup: {e}")


async def post_init(application: Application) -> None:
    """Inisialisasi awal saat bot mulai berjalan."""
    # Bersihkan file sampah sisa sesi sebelumnya saat bot pertama kali dinyalakan
    deleted = config.clean_old_temp_files(max_age_seconds=0)
    if deleted > 0:
        logger.info(f"🧹 Startup Cleanup: Menghapus {deleted} file sampah lama di temp.")
    
    # Jalankan background cleaner berkala
    asyncio.create_task(periodic_temp_cleanup())


def main() -> None:
    """Entry point untuk menjalankan bot"""
    if not config.BOT_TOKEN or config.BOT_TOKEN == "GANTI_DENGAN_TOKEN_BOT_ANDA":
        print("=" * 60)
        print("❌ ERROR: BOT_TOKEN belum diisi!")
        print("Silakan buka file '.env' dan masukkan token bot dari @BotFather.")
        print("Contoh isi .env:")
        print("BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        print("=" * 60)
        return

    print("🚀 Menjalankan TikTok AI Bypass Bot...")
    app = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("tips", tips_command))
    app.add_handler(CommandHandler("mode", mode_command))

    # Video messages
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video_message))

    # Inline button callbacks
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    print("✅ Bot siap! Menunggu kiriman video dari pengguna...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
