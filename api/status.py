from http.server import BaseHTTPRequestHandler
import json
import os
import subprocess

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        ffmpeg_status = "unknown"
        ffmpeg_version = ""
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            res = subprocess.run([ffmpeg_exe, "-version"], capture_output=True, text=True, timeout=5)
            ffmpeg_status = "available"
            ffmpeg_version = res.stdout.splitlines()[0] if res.stdout else ""
        except Exception as e:
            ffmpeg_status = f"error: {str(e)}"

        response_data = {
            "status": "online",
            "service": "TikTok AI Video Bypass API",
            "bot_username": "@boteraserai_bot",
            "ffmpeg": ffmpeg_status,
            "ffmpeg_version": ffmpeg_version,
            "environment": "vercel_serverless" if os.getenv("VERCEL") else "local"
        }
        self.wfile.write(json.dumps(response_data, indent=2).encode('utf-8'))
