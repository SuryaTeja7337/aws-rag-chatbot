from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        SimpleHTTPRequestHandler.end_headers(self)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8080), CORSRequestHandler)
    print('Server running at http://localhost:8080/')
    server.serve_forever()
