import http.server
import socketserver
import json
import os
import urllib.parse

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
GRANTHALU_DIR = os.path.dirname(DIRECTORY)

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
            self.end_headers()
            
            files = []
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
                    self.end_headers()
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.wfile.write(f.read().encode('utf-8'))
                    return
            
            self.send_error(404, "File not found")
            return

        return super().do_GET()

os.chdir(DIRECTORY)
with socketserver.TCPServer(("", PORT), TeluguHandler) as httpd:
    print(f"Serving at port {PORT}")
    print(f"Granthalu directory: {GRANTHALU_DIR}")
    httpd.serve_forever()
