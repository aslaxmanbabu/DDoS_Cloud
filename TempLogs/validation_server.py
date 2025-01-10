from flask import Flask, request, jsonify, redirect
import time
import logging
import os

app = Flask(__name__)

captcha_data = {"captcha": "12345"}  # Example CAPTCHA for testing
request_timestamps = {}  # Store timestamps of requests for each IP
# File to store suspicious IPs
suspicious_ips_file = "suspicious_ips.txt"

# Set up logging
logging.basicConfig(level=logging.INFO)


def add_ip_to_suspicious_list(ip):
    """
    Add an IP to the suspicious list file if it's not already there,
    and reload NGINX after adding the IP.
    """
    ip_added = False
    with open(suspicious_ips_file, "a+") as file:
        file.seek(0)
        existing_ips = set(file.read().splitlines())
        deny_ip = f"deny {ip};"
        if deny_ip not in existing_ips:
            file.write(f"deny {ip};\n")
            ip_added = True
            logging.warning(f"Added IP {ip} to suspicious list.")

    # Reload NGINX only if a new IP was added
    if ip_added:
        reload_nginx()


def reload_nginx():
    """
    Reload NGINX to apply changes.
    """
    try:
        os.system("nginx -s reload")
        logging.info("NGINX reloaded successfully.")
    except Exception as e:
        logging.error(f"Error reloading NGINX: {e}")


@app.route("/", methods=["GET"])
def serve_captcha():
    """
    Serve the CAPTCHA challenge.
    """
    client_ip = request.remote_addr

    # Track the request timestamp for the IP
    if client_ip not in request_timestamps:
        request_timestamps[client_ip] = time.time()
    else:
        # Check if the client has already requested within 5 seconds
        elapsed_time = time.time() - request_timestamps[client_ip]
        if elapsed_time < 5:
            # Add IP to suspicious list if a new request comes within 5 seconds
            add_ip_to_suspicious_list(client_ip)
            return jsonify({"error": "Your IP is blocked due to suspicious activity."}), 403

    return """
    <html>
    <body>
        <h2>Complete CAPTCHA to Proceed</h2>
        <form action="/validate" method="POST">
            <label for="captcha">Enter CAPTCHA: 12345</label>
            <input type="text" id="captcha" name="captcha">
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    """


@app.route("/validate", methods=["POST"])
def validate_captcha():
    """
    Validate CAPTCHA and ensure 5 seconds have passed since the initial request.
    """
    client_ip = request.remote_addr
    current_time = time.time()

    # Ensure 5 seconds have passed since the initial request
    if client_ip in request_timestamps:
        elapsed_time = current_time - request_timestamps[client_ip]
        if elapsed_time < 5:
            # Add to suspicious IP list if conditions are violated
            add_ip_to_suspicious_list(client_ip)
            return jsonify({"error": "Please wait 5 seconds before submitting."}), 403

    # Check CAPTCHA validity
    user_input = request.form.get("captcha")
    nginx_host = request.host

    if user_input == captcha_data["captcha"]:
        # CAPTCHA is correct. Return a success response with custom header
        response = redirect(f"http://{nginx_host}/")
        response.set_cookie("captcha_status", "valid",
                            max_age=3600)  # Set for 1 hour
        return response
    else:
        return jsonify({"error": "Invalid CAPTCHA. Try again."}), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
