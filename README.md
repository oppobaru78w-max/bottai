# 🤖 TikTok AI Video Bypass - Telegram Bot

Bot Telegram otomatis untuk **menghilangkan jejak & deteksi AI pada video TikTok** yang dibuat menggunakan AI Generator (*Sora, Kling AI, Runway Gen-3, Luma Dream Machine, Midjourney, CapCut AI, Haiper, Pika, dsb.*).

Bot ini membersihkan metadata C2PA, mengacak grid piksel difusi matematis, menyuntikkan noise optik sensor kamera nyata, dan menyelaraskan spektrum audio agar video Anda terdaftar sebagai rekaman kamera alami dan **tidak otomatis diberi label "AI-generated content"** oleh algoritma TikTok.

---

## 🌟 Fitur Utama & Cara Kerja Anti-Deteksi

| Fitur | Penjelasan Teknis & Manfaat |
|---|---|
| 🛡️ **Pembersihan C2PA & Provenance** | Menghapus 100% metadata global, EXIF, XMP, UUID, dan tag container rahasia yang disematkan oleh generator AI. |
| 🔬 **Resampling Grid Piksel (Micro-Zoom)** | Melakukan zoom 1% - 2% dengan kalkulasi ulang matriks piksel, menghancurkan pola grid laten yang dicari oleh model detektor AI. |
| 📸 **Injeksi Sensor Grain (ISO Camera Noise)** | Menambahkan butiran noise optik alami (*time-varying sensor noise*) untuk menghapus kehalusan artifisial khas AI. |
| 🎨 **Micro-Color Histogram Shifting** | Menyesuaikan kontras, saturasi, dan gamma tipis agar histogram warna video berbeda dari template bawaan AI. |
| 🎵 **Audio Pitch & Tempo Shifting** | Menggeser mikro kecepatan suara (`atempo=1.008`) dan menormalkan loudness standar TikTok (`loudnorm`) untuk lolos deteksi suara sintetis (*ElevenLabs/OpenAI*). |
| ⚡ **4 Pilihan Mode Pemrosesan** | **Standar** (Rekomendasi), **Agresif** (Super Bypass), **Sinematik** (35mm Grain), dan **Hanya C2PA** (Instan 1-2 detik). |

---

## 🚀 Panduan Instalasi & Penggunaan

### 1. Buat Bot di Telegram & Dapatkan Token
1. Buka aplikasi Telegram dan cari akun resmi **[@BotFather](https://t.me/BotFather)**.
2. Kirim pesan `/newbot`.
3. Beri nama bot Anda (contoh: `TikTok Humanizer Bot`).
4. Beri username bot yang berakhiran `bot` (contoh: `tiktok_nobypass_bot`).
5. BotFather akan memberikan **HTTP API Token** (contoh: `7123456789:AAHk...`). Salin token tersebut.

### 2. Konfigurasi Token Bot
Token bot Anda telah otomatis terpasang di file `.env`:
```env
BOT_TOKEN=8107353822:AAEh67cxdsjT1mXLowH8XP9q0gv-CU70GJE
MAX_FILE_SIZE_MB=20
```
> 🔒 **Keamanan**: File `.env` sudah masuk ke `.gitignore` sehingga tidak akan pernah bocor atau terunggah saat Anda push ke GitHub.

---

## 🧹 Sistem Pembersihan Otomatis (Anti Penyimpanan Penuh)

Bot ini dirancang dengan **Garansi 0% Penumpukan Data (Zero Clutter)**:
1. **Pembersihan Seketika**: Setiap kali video selesai diproses dan dikirimkan ke Telegram, file video mentah dan video hasil di folder `temp/` **langsung dihapus seketika** oleh sistem (`finally:` unlinking).
2. **Background Auto-Purge**: Bot menjalankan pembersih otomatis setiap 30 menit di latar belakang untuk menghapus sisa file sementara yang usianya lebih dari batas waktu (otomatis dibersihkan sebelum mencapai 24 jam).
3. **Startup Cleaner**: Setiap kali bot dijalankan ulang, seluruh file sampah sisa sesi lama otomatis dihapus total.
4. **Cloud Ephemeral Storage**: Pada hosting cloud (seperti Vercel atau Render), direktori sementara `/tmp` akan di-reset otomatis oleh platform saat container berputar, menjamin ruang penyimpanan website/server **tidak akan pernah penuh**.

---

## 🌐 Panduan Deploy ke GitHub & Hosting (Vercel / Render)

### Langkah A: Push ke GitHub Anda
1. Buat repositori baru di akun GitHub Anda (misal nama repo: `tiktok-ai-bypass-bot`).
2. Di terminal folder proyek ini, jalankan perintah berikut (ganti `USERNAME` dengan username GitHub Anda):
```bash
git remote add origin https://github.com/USERNAME/tiktok-ai-bypass-bot.git
git push -u origin main
```

---

### Langkah B: Deploy 100% Gratis di Vercel (24/7 Nonstop via Webhook)
1. Repositori GitHub: `https://github.com/oppobaru78w-max/bottai`
2. Di [vercel.com](https://vercel.com), proyek terhubung otomatis dan mendeploy branch `main`.
3. Endpoint Telegram Webhook berjalan otomatis di:
   - `https://bottai-eel9.vercel.app/api/webhook`
4. Setup webhook otomatis terkonfigurasi ke server Telegram. Bot akan aktif 24 jam nonstop di cloud Vercel meskipun komputer/laptop Anda dimatikan!
5. Untuk mengecek status bot & FFmpeg:
   - `https://bottai-eel9.vercel.app/api/status`


---

## 📱 Menu Perintah di Bot Telegram

- `/start` : Memulai bot & menampilkan instruksi lengkap.
- `/tips` : 5 Tips penting agar video AI lolos deteksi dan cepat tembus FYP.
- `/mode` : Memilih preset default (Standar / Agresif / Sinematik / Hanya C2PA / Tanya Setiap Kirim).
- `/help` : Penjelasan teknis deteksi AI dan cara bot bekerja.

---

## 💡 5 Tips Rahasia Agar Video AI Lolos & FYP di TikTok

1. **Gunakan Musik Tren TikTok (Wajib)** 🎵  
   Saat hendak memposting video di aplikasi TikTok, tambahkan musik yang sedang viral dari perpustakaan musik resmi TikTok.  
   *Trik:* Jika video Anda sudah memiliki narasi/suara sendiri, kecilkan volume musik TikTok ke **1% - 3%**. Algoritma TikTok akan memvalidasi audio Anda sebagai audio legal dari sistem mereka.

2. **Matikan Opsi 'Konten Dibuat AI'** ❌  
   Sebelum menekan tombol posting, periksa bagian pengaturan lainnya dan pastikan tombol *'AI-generated content / Konten yang dibuat AI'* dalam keadaan **MATI (OFF)**.

3. **Gunakan Elemen Native Editor TikTok** ✍️  
   Tambahkan 1 stiker kecil atau judul teks menggunakan fitur teks bawaan aplikasi TikTok. Sistem TikTok sangat menyukai video yang disunting menggunakan aplikasinya.

4. **Beri Jeda Waktu Antar Upload** ⏱️  
   Jangan mengunggah 5 video sekaligus dalam 10 menit. Berikan jeda 1 hingga 2 jam per video agar akun Anda tidak dideteksi sebagai akun spam bot.

5. **Interaksi di 30 Menit Pertama** 💬  
   Balas komentar penonton pertama yang masuk agar algoritma TikTok membaca video Anda memiliki tingkat interaksi (*engagement rate*) yang tinggi.

---

## ⚠️ Catatan Batasan Ukuran File Telegram
API resmi bot Telegram membatasi pengunduhan file maksimal **20 MB**.  
Jika video Anda berukuran lebih dari 20 MB:
- Potong durasi video ke bagian inti (video TikTok berdurasi 30-60 detik memiliki retensi terbaik).
- Atau kompres resolusi sedikit sebelum dikirimkan ke bot.
