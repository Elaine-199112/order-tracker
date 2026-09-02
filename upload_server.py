#!/usr/bin/env python3
"""图片上传服务 — 监听 9002，接收款式图片上传。

POST /upload  (multipart/form-data, 字段名任意)  -> 保存到 images/ 目录，返回 {"ok":true,"url":"/images/xxx.jpg"}
图片访问走 9001（python http.server 直接服务 order-tracker 目录），无需本服务处理 GET。
"""
import os
import json
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

IMAGES_DIR = "/home/ubuntu/order-tracker/images"
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
}
MAX_SIZE = 20 * 1024 * 1024  # 20MB


class UploadHandler(BaseHTTPRequestHandler):
    def _send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path.rstrip("/") != "/upload":
            self._send_json(404, {"ok": False, "error": "not found"})
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json(400, {"ok": False, "error": "需要 multipart/form-data"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self._send_json(400, {"ok": False, "error": "无效的 Content-Length"})
            return
        if length <= 0 or length > MAX_SIZE:
            self._send_json(400, {"ok": False, "error": "文件过大或为空（最大 20MB）"})
            return

        body = self.rfile.read(length)

        from email.parser import BytesParser
        from email import policy
        msg = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: " + content_type.encode("utf-8", "replace") + b"\r\n\r\n" + body
        )

        os.makedirs(IMAGES_DIR, exist_ok=True)

        for part in msg.iter_parts():
            ctype = part.get_content_type()
            if ctype not in ALLOWED_TYPES:
                continue
            data = part.get_payload(decode=True)
            if not data or not isinstance(data, bytes):
                continue
            if len(data) > MAX_SIZE:
                self._send_json(400, {"ok": False, "error": "文件过大"})
                return
            ext = ALLOWED_TYPES[ctype]
            fname = uuid.uuid4().hex + ext
            with open(os.path.join(IMAGES_DIR, fname), "wb") as f:
                f.write(data)
            self._send_json(200, {"ok": True, "url": "/images/" + fname})
            return

        self._send_json(400, {"ok": False, "error": "未找到有效的图片文件"})

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    os.makedirs(IMAGES_DIR, exist_ok=True)
    HTTPServer(("0.0.0.0", 9002), UploadHandler).serve_forever()
