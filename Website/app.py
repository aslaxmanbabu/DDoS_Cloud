import os
from aiohttp import web
import logging
from datetime import datetime, timedelta
import aiohttp_session
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import secrets  # Use secrets to generate a random key

# Configure logging
logging.basicConfig(
    filename="D:\Official\Final\Implementation\TempLogs\server_logs.txt",
    level=logging.INFO,
    format="%(message)s"
)
logging.getLogger("aiohttp.access").setLevel(logging.CRITICAL)

# Define the static and template directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# Generate a random key (32 bytes for AES-256)
KEY = secrets.token_bytes(32)  # Using 32 random bytes

# Session timeout duration (5 minutes)
SESSION_TIMEOUT = timedelta(minutes=5)

# Helper to render HTML pages


async def render_html(request, filename):
    try:
        with open(os.path.join(TEMPLATE_DIR, filename), "r", encoding="utf-8") as file:
            content = file.read()
        return web.Response(text=content, content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="<h1>404: Page Not Found</h1>", status=404, content_type="text/html")

# Route handlers


async def index(request):
    # Set session flag for valid pages and reset session expiry time
    session = await aiohttp_session.get_session(request)
    session['valid_source'] = True
    # Store timestamp of session creation
    session['timestamp'] = datetime.now().isoformat()
    return await render_html(request, "index.html")


async def menu(request):
    # Check session flag and session expiry time
    session = await aiohttp_session.get_session(request)
    timestamp = session.get('timestamp')
    if not timestamp or datetime.fromisoformat(timestamp) + SESSION_TIMEOUT < datetime.now():
        session.clear()  # Invalidate session if expired
        return web.HTTPForbidden(text="Forbidden: Session has expired.")

    # Session is still valid, reset expiry time
    session['timestamp'] = datetime.now().isoformat()
    return await render_html(request, "menu.html")


async def embedding(request):
    # Set session flag for valid pages and reset session expiry time
    session = await aiohttp_session.get_session(request)
    session['valid_source'] = True
    # Store timestamp of session creation
    session['timestamp'] = datetime.now().isoformat()
    return await render_html(request, "embedding.html")


async def empty(request):
    return await render_html(request, "empty.html")


async def widgets(request):
    # Set session flag for valid pages and reset session expiry time
    session = await aiohttp_session.get_session(request)
    session['valid_source'] = True
    # Store timestamp of session creation
    session['timestamp'] = datetime.now().isoformat()
    return await render_html(request, "widgets.html")


async def footer(request):
    # Check session flag and session expiry time
    session = await aiohttp_session.get_session(request)
    timestamp = session.get('timestamp')
    if not timestamp or datetime.fromisoformat(timestamp) + SESSION_TIMEOUT < datetime.now():
        session.clear()  # Invalidate session if expired
        return web.HTTPForbidden(text="Forbidden: Session has expired.")

    # Session is still valid, reset expiry time
    session['timestamp'] = datetime.now().isoformat()
    return await render_html(request, "footer.html")

# Middleware to log requests


@web.middleware
async def log_requests_middleware(request, handler):
    # Get client IP and request details
    client_ip = request.headers.get("X-Real-IP", request.remote or "unknown")
    request_line = f"{request.method} {request.path} HTTP/{request.version.major}.{request.version.minor}"
    response = await handler(request)

    # Log the request and response details for allowed routes
    if request.path in ['/', '/embedding', '/widgets']:
        log_data = {
            "clientip": client_ip,
            "asctime": datetime.now().strftime("%d/%b/%Y:%H:%M:%S"),
            "requestline": request_line,
            "status_code": response.status,
        }

        log_message = f"{log_data['clientip']} - - [{log_data['asctime']}] \"{log_data['requestline']}\" {log_data['status_code']} -"
        logging.info(log_message)

    return response

# Create and configure the application


def create_app():
    # Create EncryptedCookieStorage with the random key for session encryption
    storage = EncryptedCookieStorage(KEY)

    # Create session middleware
    session_middleware_instance = session_middleware(storage)

    app = web.Application(
        middlewares=[session_middleware_instance, log_requests_middleware])

    # Routes for pages
    app.router.add_get("/", index)
    app.router.add_get("/menu", menu)
    app.router.add_get("/embedding", embedding)
    app.router.add_get("/empty", empty)
    app.router.add_get("/widgets", widgets)
    app.router.add_get("/footer", footer)

    # Serve static files
    app.router.add_static("/static", STATIC_DIR)

    return app


# Run the application
if __name__ == "__main__":
    app = create_app()
    logging.info("Starting server at http://0.0.0.0:8080")
    web.run_app(app, port=8080)
