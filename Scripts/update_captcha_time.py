from http.server import SimpleHTTPRequestHandler, HTTPServer
import json
import time


class CaptchaUpdateHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/update_captcha_time":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Extract the start time from the POST data
            data = json.loads(post_data)
            captcha_start_time = data["start_time"]

            # Now update the Nginx shared memory with the CAPTCHA start time
            # Here you can directly interact with Nginx (via a small Lua script or other mechanism)
            # to set the shared memory value

            print(f"Captcha start time updated to: {captcha_start_time}")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "success"}')


def run(server_class=HTTPServer, handler_class=CaptchaUpdateHandler):
    server_address = ('', 8081)  # Use a different port for the update
    httpd = server_class(server_address, handler_class)
    print("Starting server to update CAPTCHA start time...")
    httpd.serve_forever()


if __name__ == '__main__':
    run()
