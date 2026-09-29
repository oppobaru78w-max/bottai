from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response_data = {
            "status": "online",
            "service": "TikTok AI Video Bypass API",
            "bot_username": "@boteraserai_bot",
            "storage_status": "auto_cleaned",
            "cleanup_retention": "immediate_and_periodic",
            "message": "Bot aktif dan penyimpanan otomatis dibersihkan secara real-time."
        }
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
