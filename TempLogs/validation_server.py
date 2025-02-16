from flask import Flask, request, redirect, jsonify

app = Flask(__name__)

# Example CAPTCHA for testing
captcha_data = {"captcha": "12345"}


@app.route("/", methods=["GET"])
def serve_captcha():
    """
    Serve the CAPTCHA challenge with a 5-second timer.
    """
    original_request = request.args.get("redirect_uri", "/")  # Default to "/"

    return f"""
    <html>
    <head>
        <script>
            window.onload = function() {{
                const submitButton = document.getElementById("submit-btn");
                const timerDisplay = document.getElementById("timer");
                let countdown = 5;

                submitButton.disabled = true;

                const interval = setInterval(() => {{
                    timerDisplay.innerText = "Please wait " + countdown + " seconds before submitting.";
                    countdown--;

                    if (countdown < 0) {{
                        clearInterval(interval);
                        submitButton.disabled = false;
                        timerDisplay.innerText = "You can now submit the CAPTCHA.";
                    }}
                }}, 1000);
            }};
        </script>
    </head>
    <body>
        <h2>Complete CAPTCHA to Proceed</h2>
        <p id="timer">Initializing timer...</p>
        <form action="/validate" method="POST">
            <input type="hidden" name="original_request" value="{original_request}">
            <label for="captcha">Enter CAPTCHA: 12345</label>
            <input type="text" id="captcha" name="captcha" required>
            <button type="submit" id="submit-btn">Submit</button>
        </form>
    </body>
    </html>
    """


@app.route("/validate", methods=["POST"])
def validate_captcha():
    """
    Validate CAPTCHA and redirect back to the requested endpoint if successful.
    """
    user_input = request.form.get("captcha")
    original_request = request.form.get(
        "original_request", "/")  # Default to "/"

    if user_input == captcha_data["captcha"]:
        # CAPTCHA is correct. Set a success cookie
        redirect_url = f"http://{request.host}{original_request}"
        response = redirect(redirect_url)

        response.set_cookie("captcha_status", "valid",
                            max_age=3600)  # Set for 1 hour
        return response
    else:
        # Invalid CAPTCHA
        return jsonify({"error": "Invalid CAPTCHA. Try again."}), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
