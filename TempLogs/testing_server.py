from aiohttp import web, ClientSession
import logging
from datetime import datetime, timedelta
import hashlib

# Configure logging
logging.basicConfig(filename='server_logs.txt',
                    level=logging.INFO, format='%(message)s')
logging.getLogger("aiohttp.access").setLevel(logging.CRITICAL)

NGINX_URL = "http://127.0.0.1:80"  # NGINX Load Balancer
WEBHOOK_URL = "http://127.0.0.1:5000"  # Flask Webhook server

# Define the session timeout (e.g., 5 minutes)
SESSION_TIMEOUT = timedelta(minutes=5)

# Store sessions and their last validation timestamp
CAPTCHA_SESSIONS = {}


async def check_nginx():
    """
    Check if NGINX is active by querying its status endpoint.
    """
    try:
        async with ClientSession() as session:
            async with session.get(f"{WEBHOOK_URL}/nginx_status") as response:
                status = await response.json()
                return status.get('status') == 'NGINX is running.'
    except Exception as e:
        logging.error(f"Validation error: {e}")
        return False


async def validate_with_nginx(request, session_id):
    """
    Redirect to NGINX for CAPTCHA validation, setting the session ID as a cookie.
    """
    try:
        # Log the received session_id before redirecting
        logging.info(f"Redirecting to NGINX with session_id: {session_id}")

        # Log the received data
        data = await request.post()
        logging.info(
            f"Redirecting to CAPTCHA validation page with data: {data}")

        # Create the redirection response
        response = web.Response(
            text="Redirecting to CAPTCHA challenge page.", status=302
        )
        response.headers["Location"] = f"{NGINX_URL}"

        # Set session ID as cookie
        response.set_cookie("session_id", session_id)

        # Extract session_id from the Set-Cookie header to log it
        cookies = response.cookies
        session_cookie = cookies.get('session_id', None)

        if session_cookie:
            logging.info(f"Session ID set in response: {session_cookie.value}")

        # Log the response headers sent to NGINX
        logging.info(f"Response headers sent to NGINX: {response.headers}")

        return response
    except Exception as e:
        logging.error(f"Validation error: {e}")
        # Redirect to an error page if something goes wrong
        return web.HTTPFound("/error_page")


async def handle_request(request):
    """
    Main request handler. Redirects to NGINX or checkpoint based on the status of NGINX.
    """
    client_ip = request.remote or "unknown"
    request_line = f"{request.method} {request.path} HTTP/{request.version.major}.{request.version.minor}"
    log_data = {
        "clientip": client_ip,
        "asctime": datetime.now().strftime("%d/%b/%Y:%H:%M:%S"),
        "requestline": request_line,
        "status_code": None,
    }

    # Extract query parameters for session validation
    session_id = request.query.get("session_id")
    validated = request.query.get("validated")

    # Ensure NGINX is active before proceeding
    nginx_active = await check_nginx()
    logging.info(
        f"Nginx Status:  {nginx_active}."
    )
    if nginx_active:
        if not session_id:
            # If no session_id exists, create one and log it
            session_id = hashlib.md5(client_ip.encode()).hexdigest()
            logging.info(
                f"Session not found for {client_ip}. Creating new session {session_id}."
            )

            # Proceed with CAPTCHA validation for the new session
            return await validate_with_nginx(request, session_id)

        if validated == "true":
            # If session is validated, perform the desired redirection logic
            logging.info(
                f"Session {session_id} validated. Proceeding with main content."
            )
            # After successful CAPTCHA validation, proceed with the main website content
            response = web.Response(
                text="Welcome to the secure test website!", status=200
            )
            # Invalidate the session cookie after validation
            response.del_cookie("session_id")
            log_data["status_code"] = 200
        else:
            # If session is not validated, proceed with CAPTCHA validation logic
            logging.info(
                f"Session {session_id} not validated. Redirecting to CAPTCHA."
            )
            return await validate_with_nginx(request, session_id)
    else:
        # Redirect to a fallback checkpoint URL if NGINX is inactive
        response = web.Response(
            text="NGINX is inactive. Redirecting to checkpoint.", status=200
        )
        log_data["status_code"] = 200

    log_message = f"{log_data['clientip']} - - [{log_data['asctime']}] \"{log_data['requestline']}\" {log_data['status_code']} -"
    logging.info(log_message)
    return response


def create_app():
    """
    Create and configure the aiohttp application.
    """
    app = web.Application()
    app.router.add_post("/{tail:.*}", handle_request)
    app.router.add_route('GET', '/{tail:.*}', handle_request)
    return app


if __name__ == "__main__":
    app = create_app()
    print("Starting aiohttp server at http://0.0.0.0:8080")
    web.run_app(app, host="0.0.0.0", port=8080)
