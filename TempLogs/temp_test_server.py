from aiohttp import web
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(filename='server_logs.txt',
                    level=logging.INFO, format='%(message)s')
logging.getLogger("aiohttp.access").setLevel(logging.CRITICAL)


async def test_webpage(request):
    """
    Display a simple test webpage, log the request details, and debug headers.
    """
    # Get client IP from X-Real-IP or fallback to request.remote
    client_ip = request.headers.get('X-Real-IP', request.remote or "unknown")
    request_line = f"{request.method} {request.path} HTTP/{request.version.major}.{request.version.minor}"

    # Log the request details
    log_data = {
        "clientip": client_ip,
        "asctime": datetime.now().strftime("%d/%b/%Y:%H:%M:%S"),
        "requestline": request_line,
        "status_code": 200,  # Assuming 200 OK for this request
    }

    log_message = f"{log_data['clientip']} - - [{log_data['asctime']}] \"{log_data['requestline']}\" {log_data['status_code']} -"
    logging.info(log_message)

    # Return the test webpage for GET requests
    if request.method == 'GET':
        return web.Response(
            text="<html><body><h2>Welcome to the Test Webpage!</h2></body></html>",
            content_type="text/html",
            status=200,
        )
    # Handle POST requests (example)
    elif request.method == 'POST':
        data = await request.post()  # Get POST data (example)
        return web.Response(
            text=f"<html><body><h2>Received POST data: {data}</h2></body></html>",
            content_type="text/html",
            status=200,
        )


def create_app():
    """
    Create the aiohttp app and set up routes.
    """
    app = web.Application()
    app.router.add_get("/", test_webpage)  # Route for the test webpage (GET)
    app.router.add_post("/", test_webpage)  # Route for handling POST requests
    return app


if __name__ == "__main__":
    app = create_app()
    logging.info("Starting test server at http://0.0.0.0:8080")
    web.run_app(app, host="0.0.0.0", port=8080)
