import http.server
import socketserver
import json
import os
import urllib.parse
import urllib.request

# Use PORT from environment variable or default to 8000
PORT = int(os.environ.get("PORT", 8000))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
# Data is now inside the web-app/data directory
GRANTHALU_DIR = os.path.join(DIRECTORY, "data")

class TeluguHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Serve index.html for the root
        if path == "/":
            return os.path.join(DIRECTORY, "index.html")
        return super().translate_path(path)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        
        # API to list files
        if url.path == "/api/files":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            files = []
            if os.path.exists(GRANTHALU_DIR):
                for f in os.listdir(GRANTHALU_DIR):
                    if f.endswith(".txt"):
                        files.append(f)
            
            self.wfile.write(json.dumps(sorted(files)).encode())
            return
            
        # API to get file content
        if url.path == "/api/file":
            query = urllib.parse.parse_qs(url.query)
            filename = query.get("name", [None])[0]
            
            if filename and filename.endswith(".txt"):
                filepath = os.path.join(GRANTHALU_DIR, filename)
                if os.path.exists(filepath):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.wfile.write(f.read().encode('utf-8'))
                    return
            
            self.send_error(404, "File not found")
            return

        # Proxy for Google TTS to avoid CORS
        if url.path == "/api/tts":
            query = urllib.parse.parse_qs(url.query)
            text = query.get("text", [""])[0]
            lang = query.get("lang", ["te"])[0]
            if not text:
                self.send_error(400, "No text provided")
                return
            # Limit text length to 200 chars per request (Google TTS limit)
            text = text[:200]
            tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=tw-ob&q={urllib.parse.quote(text)}"
            try:
                req = urllib.request.Request(tts_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    audio_data = resp.read()
                self.send_response(200)
                self.send_header('Content-type', 'audio/mpeg')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(audio_data)
            except Exception as e:
                self.send_error(500, f"TTS error: {e}")
            return

        return super().do_GET()

os.chdir(DIRECTORY)
# Use 0.0.0.0 to allow external access in Render
with socketserver.TCPServer(("0.0.0.0", PORT), TeluguHandler) as httpd:
    print(f"Serving at port {PORT}")
    print(f"Granthalu directory: {GRANTHALU_DIR}")
    httpd.serve_forever()
