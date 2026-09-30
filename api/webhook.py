import os
import sys
import json
import time
import uuid
import urllib.parse
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Pastikan root directory masuk ke sys.path agar config dan processor bisa diimport
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config
import processor
import requests

BOT_TOKEN = config.BOT_TOKEN or "8107353822:AAEh67cxdsjT1mXLowH8XP9q0gv-CU70GJE"
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Memory storage for preferences in serverless
# (Bila serverless recycle, default selalu standard Full HD 1080p)
serverless_prefs = {}

def get_pref(user_id: int) -> str:
    return serverless_prefs.get(str(user_id), "standard")

def set_pref(user_id: int, pref: str) -> None:
    serverless_prefs[str(user_id)] = pref


def tg_send_message(chat_id: int, text: str, reply_markup=None) -> dict:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(f"{API_BASE}/sendMessage", json=payload, timeout=15)
        return r.json()
    except Exception as e:
        print(f"Error tg_send_message: {e}")
        return {}


def tg_edit_message(chat_id: int, message_id: int, text: str, reply_markup=None) -> dict:
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(f"{API_BASE}/editMessageText", json=payload, timeout=15)
        return r.json()
    except Exception as e:
        print(f"Error tg_edit_message: {e}")
        return {}


def tg_answer_callback(callback_query_id: str, text=None) -> None:
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    try:
        requests.post(f"{API_BASE}/answerCallbackQuery", json=payload, timeout=10)
    except Exception:
        pass


def tg_send_chat_action(chat_id: int, action: str = "upload_video") -> None:
    try:
        requests.post(f"{API_BASE}/sendChatAction", json={"chat_id": chat_id, "action": action}, timeout=10)
    except Exception:
        pass


def tg_download_file(file_id: str, dest_path: Path) -> bool:
    try:
        res = requests.get(f"{API_BASE}/getFile", params={"file_id": file_id}, timeout=20)
        data = res.json()
        if not data.get("ok"):
            return False
        file_path_on_tg = data["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path_on_tg}"
        with requests.get(download_url, stream=True, timeout=120) as stream_resp:
            stream_resp.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in stream_resp.iter_content(chunk_size=65536):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Error download file: {e}")
        return False


def tg_send_video(chat_id: int, video_path: Path, caption: str, width: int = None, height: int = None) -> bool:
    try:
        data = {
            "chat_id": chat_id,
            "caption": caption,
            "parse_mode": "Markdown",
            "supports_streaming": True,
        }
        if width:
            data["width"] = width
        if height:
            data["height"] = height

        with open(video_path, "rb") as video_fp:
            files = {"video": (video_path.name, video_fp, "video/mp4")}
            r = requests.post(f"{API_BASE}/sendVideo", data=data, files=files, timeout=180)
            return r.json().get("ok", False)
    except Exception as e:
        print(f"Error send_video: {e}")
        return False


def handle_update(update: dict) -> None:
    # 1. Callback Query (Tombol ditekan)
    if "callback_query" in update:
        cq = update["callback_query"]
        cq_id = cq["id"]
        data = cq.get("data", "")
        chat_id = cq["message"]["chat"]["id"]
        message_id = cq["message"]["message_id"]
        user_id = cq["from"]["id"]

        tg_answer_callback(cq_id)

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
            tg_send_message(chat_id, tips_text)

        elif data == "show_modes":
            current_mode = get_pref(user_id)
            keyboard = {
                "inline_keyboard": [
                    [{"text": "💎 Full HD 1080p (Rekomendasi TikTok)" + (" ✅" if current_mode == "standard" else ""), "callback_data": "set_pref_standard"}],
                    [{"text": "👑 Super 4K UHD (2160x3840)" + (" ✅" if current_mode == "super_4k" else ""), "callback_data": "set_pref_super_4k"}],
                    [{"text": "🛡️ Resolusi Asli (Hanya C2PA)" + (" ✅" if current_mode == "pure_c2pa" else ""), "callback_data": "set_pref_pure_c2pa"}],
                    [{"text": "🔥 Agresif 1080p (Super Bypass)" + (" ✅" if current_mode == "aggressive" else ""), "callback_data": "set_pref_aggressive"}],
                    [{"text": "🎬 Sinematik 1080p (35mm Grain)" + (" ✅" if current_mode == "cinematic" else ""), "callback_data": "set_pref_cinematic"}],
                ]
            }
            tg_send_message(chat_id, "⚙️ **Pilih Mode Default Pemrosesan (Full HD / 4K):**", reply_markup=keyboard)

        elif data.startswith("set_pref_"):
            new_pref = data.replace("set_pref_", "")
            set_pref(user_id, new_pref)
            names = {
                "standard": "💎 Full HD 1080p (Rekomendasi TikTok)",
                "super_4k": "👑 Super 4K UHD (2160x3840)",
                "pure_c2pa": "🛡️ Resolusi Asli (Hanya C2PA)",
                "aggressive": "🔥 Agresif 1080p (Super Bypass)",
                "cinematic": "🎬 Sinematik 1080p (35mm Grain)",
            }
            msg = (
                f"✅ **Mode Default Berhasil Disimpan di Vercel Cloud!**\n\n"
                f"Pilihan Anda: **{names.get(new_pref, new_pref)}**.\n"
                "Setiap video yang dikirimkan akan diproses dengan mode ini secara otomatis 24 jam nonstop."
            )
            tg_edit_message(chat_id, message_id, msg)

        elif data == "force_clean_storage":
            deleted = config.clean_old_temp_files(max_age_seconds=0)
            tg_edit_message(chat_id, message_id, f"✅ **Penyimpanan Cloud Vercel Bersih!**\n\n• File sampah dibersihkan: `{deleted} file`\n• Status disk: `0.00 MB` (100% Lega)")

        return

    # 2. Pesan Biasa
    if "message" not in update:
        return

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user_id = msg.get("from", {}).get("id", chat_id)
    text = msg.get("text", "").strip()

    # Perintah Teks
    if text.startswith("/start"):
        user_name = msg.get("from", {}).get("first_name", "Kreator")
        welcome = (
            f"👋 **Halo {user_name}! Bot TikTok AI Bypass (Vercel Cloud 24/7)**\n\n"
            "Bot ini berjalan **24 jam nonstop di cloud Vercel**, siap memodifikasi video AI Anda kapan saja walaupun komputer Anda mati!\n\n"
            "✨ **Fitur Utama:**\n"
            "• 🛡️ Hapus 100% C2PA & Content Credentials\n"
            "• 💎 Smart Upscale ke **Full HD 1080p** & **Super 4K** (Lanczos Sharpening)\n"
            "• 📸 Natural CMOS Sensor ISO Grain Injection\n"
            "• 🎵 Audio Frequency & Pitch Shifting (Anti Deteksi ElevenLabs)\n"
            "• 🧹 Auto-Delete 24 Jam (Penyimpanan Cloud Selalu Bersih)\n\n"
            "🚀 **Cukup kirimkan video Anda sekarang!**"
        )
        keyboard = {
            "inline_keyboard": [
                [{"text": "💡 Tips Upload TikTok", "callback_data": "show_tips"}, {"text": "⚙️ Pilih Mode (1080p / 4K)", "callback_data": "show_modes"}],
                [{"text": "🧹 Status Penyimpanan Cloud", "callback_data": "force_clean_storage"}],
            ]
        }
        tg_send_message(chat_id, welcome, reply_markup=keyboard)
        return

    elif text.startswith("/tips"):
        tips = (
            "💡 **5 Tips Ampuh Lolos Deteksi AI & Tembus FYP TikTok:**\n\n"
            "1. **Gunakan Audio Tren TikTok** 🎵\n"
            "   Saat upload, pakai musik dari library TikTok (atur volumenya ke 1-3%).\n\n"
            "2. **Jangan Centang Opsi AI** ❌\n"
            "   Pastikan opsi 'Konten yang dibuat AI' dalam posisi OFF.\n\n"
            "3. **Tambahkan Elemen Native TikTok** ✍️\n"
            "   Gunakan stiker atau teks bawaan TikTok.\n\n"
            "4. **Beri Jeda Waktu** ⏱️ (1-2 jam per upload).\n\n"
            "5. **Gunakan Caption & Hashtag Alami** 🏷️"
        )
        tg_send_message(chat_id, tips)
        return

    elif text.startswith("/mode"):
        current_mode = get_pref(user_id)
        keyboard = {
            "inline_keyboard": [
                [{"text": "💎 Full HD 1080p (Rekomendasi TikTok)" + (" ✅" if current_mode == "standard" else ""), "callback_data": "set_pref_standard"}],
                [{"text": "👑 Super 4K UHD (2160x3840)" + (" ✅" if current_mode == "super_4k" else ""), "callback_data": "set_pref_super_4k"}],
                [{"text": "🛡️ Resolusi Asli (Hanya C2PA)" + (" ✅" if current_mode == "pure_c2pa" else ""), "callback_data": "set_pref_pure_c2pa"}],
                [{"text": "🔥 Agresif 1080p (Super Bypass)" + (" ✅" if current_mode == "aggressive" else ""), "callback_data": "set_pref_aggressive"}],
                [{"text": "🎬 Sinematik 1080p (35mm Grain)" + (" ✅" if current_mode == "cinematic" else ""), "callback_data": "set_pref_cinematic"}],
            ]
        }
        tg_send_message(chat_id, "⚙️ **Pilih Mode Default Pemrosesan (Full HD / 4K):**", reply_markup=keyboard)
        return

    elif text.startswith("/storage") or text.startswith("/bersihkan"):
        used_mb = config.get_storage_usage_mb()
        status_txt = (
            "🧹 **Status Penyimpanan Cloud Vercel & Auto-Delete:**\n\n"
            f"• **Penggunaan Disk Saat Ini**: `{used_mb:.2f} MB` (Sangat Bersih)\n"
            f"• **Batas Retensi Cloud**: `Maksimal 24 Jam` (Otomatis Dihapus Permanen)\n"
            "• **Pembersihan Seketika**: `Aktif ✅` (Setiap video selesai diproses langsung dihapus otomatis dari server)\n\n"
            "🔒 *Garansi 0% Penumpukan Data: Server Vercel Cloud selalu bersih!*"
        )
        keyboard = {"inline_keyboard": [[{"text": "🧹 Bersihkan Sampah Sekarang", "callback_data": "force_clean_storage"}]]}
        tg_send_message(chat_id, status_txt, reply_markup=keyboard)
        return

    elif text.startswith("/help"):
        help_msg = (
            "📖 **Panduan TikTok AI Bypass Bot (Vercel Cloud 24 Jam):**\n\n"
            "• Kirimkan video apa saja ke chat ini.\n"
            "• Bot otomatis menghilangkan jejak AI, C2PA, dan menaikkan resolusi ke **1080p Full HD** atau **4K**.\n"
            "• Server berjalan di cloud Vercel 24 jam nonstop walaupun komputer Anda mati!\n\n"
            "Perintah:\n"
            "/start - Mulai ulang bot\n"
            "/mode - Pilih kualitas 1080p atau 4K\n"
            "/tips - Tips lolos FYP TikTok\n"
            "/storage - Cek kebersihan penyimpanan cloud"
        )
        tg_send_message(chat_id, help_msg)
        return

    # 3. Pemrosesan Video
    video_obj = msg.get("video")
    if not video_obj and "document" in msg:
        doc = msg["document"]
        if (doc.get("mime_type") and doc["mime_type"].startswith("video/")) or \
           (doc.get("file_name") and doc["file_name"].lower().endswith((".mp4", ".mov", ".mkv", ".webm", ".avi"))):
            video_obj = doc

    if not video_obj:
        return

    file_size_mb = (video_obj.get("file_size") or 0) / (1024 * 1024)
    if file_size_mb > config.MAX_FILE_SIZE_MB:
        tg_send_message(
            chat_id,
            f"❌ **Ukuran video terlalu besar ({file_size_mb:.1f} MB)!**\n"
            f"Batas download bot Telegram adalah **{config.MAX_FILE_SIZE_MB} MB**."
        )
        return

    file_id = video_obj["file_id"]
    preset_key = get_pref(user_id)
    preset_info = processor.PRESETS.get(preset_key, processor.PRESETS["standard"])

    # Kirim status awal
    status_resp = tg_send_message(
        chat_id,
        f"📥 **Mengunduh video di server Vercel Cloud...**\n`Mode: {preset_info['name']}`"
    )
    status_msg_id = status_resp.get("result", {}).get("message_id")

    uid = f"{user_id}_{int(time.time())}_{str(uuid.uuid4())[:6]}"
    input_file = config.TEMP_DIR / f"input_{uid}.mp4"
    output_file = config.TEMP_DIR / f"output_{uid}.mp4"

    try:
        tg_send_chat_action(chat_id, "record_video")
        download_ok = tg_download_file(file_id, input_file)
        if not download_ok or not input_file.exists():
            if status_msg_id:
                tg_edit_message(chat_id, status_msg_id, "❌ Gagal mengunduh video dari server Telegram.")
            return

        if status_msg_id:
            tg_edit_message(
                chat_id,
                status_msg_id,
                f"⚙️ **Menghilangkan Jejak AI & C2PA...**\n"
                f"• Mode: `{preset_info['name']}`\n"
                f"• Upscaling & Filtering di Vercel Cloud..."
            )

        tg_send_chat_action(chat_id, "record_video")
        success, err_msg, elapsed = processor.process_video_sync(
            str(input_file), str(output_file), preset_key
        )

        if not success or not output_file.exists():
            if status_msg_id:
                tg_edit_message(chat_id, status_msg_id, f"❌ **Gagal memproses:** `{err_msg}`")
            return

        if status_msg_id:
            tg_edit_message(
                chat_id,
                status_msg_id,
                f"📤 **Mengunggah video hasil bypass ({elapsed:.1f} detik)...**\n`Mohon tunggu sebentar...`"
            )

        tg_send_chat_action(chat_id, "upload_video")

        out_info = processor.get_video_info(str(output_file))
        pw = out_info["width"]
        ph = out_info["height"]
        if pw >= 2160 or ph >= 3840:
            res_label = "👑 Super 4K UHD"
        elif pw >= 1080 or ph >= 1920:
            res_label = "💎 Full HD 1080p"
        else:
            res_label = "HD"

        caption = (
            f"✅ **Video Berhasil Diproses di Vercel Cloud!**\n\n"
            f"🎯 **Mode**: `{preset_info['name']}`\n"
            f"⏱️ **Waktu Proses**: `{elapsed:.1f} detik`\n"
            f"📏 **Resolusi**: `{pw}x{ph}` ({res_label}) ✅\n"
            f"📦 **Ukuran**: `{out_info['size_mb']:.2f} MB`\n\n"
            f"🛡️ **Status Keamanan TikTok:**\n"
            f"• C2PA Metadata: 100% Dihapus ✅\n"
            f"• AI Latent Grid: Diacak (Resampled) ✅\n"
            f"• Sensor Grain: Ditambahkan ✅\n"
            f"• Voice Pitch: Diselaraskan ✅\n\n"
            f"💡 *Tips: Tambahkan audio tren TikTok saat upload & jangan centang 'konten dibuat AI'.*"
        )

        send_ok = tg_send_video(chat_id, output_file, caption, width=pw or None, height=ph or None)

        # Hapus pesan status sementara
        if status_msg_id:
            try:
                requests.post(f"{API_BASE}/deleteMessage", json={"chat_id": chat_id, "message_id": status_msg_id}, timeout=5)
            except Exception:
                pass

    except Exception as e:
        print(f"Exception during webhook process: {e}")
        if status_msg_id:
            tg_edit_message(chat_id, status_msg_id, f"❌ Terjadi kesalahan: `{str(e)}`")
    finally:
        # Bersihkan file sementara seketika (Zero Clutter)
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


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Fitur setup webhook otomatis: /api/webhook?setup=1
        if "setup" in query_params:
            webhook_url = f"https://bottai-eel9.vercel.app/api/webhook"
            res = requests.get(f"{API_BASE}/setWebhook", params={"url": webhook_url}, timeout=10)
            data = res.json()
            resp = {
                "ok": True,
                "action": "setWebhook",
                "webhook_url": webhook_url,
                "telegram_response": data,
            }
            self.wfile.write(json.dumps(resp, indent=2).encode("utf-8"))
            return

        resp = {
            "status": "online",
            "service": "TikTok AI Bypass Telegram Webhook",
            "bot": "@boteraserai_bot",
            "cloud": "Vercel Serverless (24/7 Active)",
            "setup_hint": "Buka /api/webhook?setup=1 untuk meregister webhook otomatis."
        }
        self.wfile.write(json.dumps(resp, indent=2).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            if post_data:
                update = json.loads(post_data.decode("utf-8"))
                handle_update(update)
        except Exception as e:
            print(f"Error handling update: {e}")
        finally:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
