from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# In-memory store for user attempts
attempts = {}


@app.route('/validate', methods=['POST'])
def validate_captcha():
    ip = request.remote_addr
    captcha_answer = request.form.get('captcha')
    current_time = time.time()

    # Check timer
    if ip in attempts and current_time - attempts[ip]['timestamp'] < 10:
        return jsonify({"status": "failed", "message": "Please wait 10 seconds before retrying."}), 429

    # Validate CAPTCHA
    if captcha_answer == "correct_answer":  # Replace with real validation
        attempts.pop(ip, None)  # Clear attempts
        return jsonify({"status": "success"})
    else:
        attempts[ip] = {"timestamp": current_time}
        return jsonify({"status": "failed", "message": "CAPTCHA incorrect."}), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)
