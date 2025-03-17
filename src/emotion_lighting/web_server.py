from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import time
import threading
import logging

# Import API components
from .api.routes import router as api_router, EmotionLightingAPI
from .api.websocket import WebSocketManager

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s")
logger = logging.getLogger("emotion_lighting")


class EmotionWebServer:
    """Web server for the Emotion Lighting system using FastAPI"""

    def __init__(
        self, emotion_tracker, touch_tracker, database, host="0.0.0.0", port=8000
    ):
        """Initialize the web server"""
        self.emotion_tracker = emotion_tracker
        self.touch_tracker = touch_tracker
        self.database = database
        self.host = host
        self.port = port
        self.running = False
        self.thread = None
        self.update_task = None

        # Create FastAPI app with minimal settings
        self.app = FastAPI(
            title="Dear Brother, ...",
            description="Control and monitor the emotion lighting system",
            version="1.0.0",
            docs_url=None,  # Disable docs for production
            redoc_url=None,  # Disable redoc for production
        )

        # Configure CORS with minimal settings
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )

        # Initialize websocket manager first
        self.ws_manager = WebSocketManager(emotion_tracker, touch_tracker, database)

        # Pass the websocket manager to EmotionLightingAPI
        self.api = EmotionLightingAPI(
            emotion_tracker, touch_tracker, database, self.ws_manager
        )

        # Set up routes
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes and WebSocket endpoint"""
        # Mount static files
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        if os.path.exists(static_dir):
            self.app.mount("/static", StaticFiles(directory=static_dir), name="static")

        # Define index route
        @self.app.get("/", response_class=HTMLResponse)
        async def get_index():
            html_path = os.path.join(static_dir, "index.html")
            if os.path.exists(html_path):
                with open(html_path, "r") as f:
                    return f.read()
            return "<html><head><title>Dear Brother, ...</title></head><body><h1>Dear Brother, ...</h1><p>Web interface is being set up.</p></body></html>"

        # Include API routes
        self.app.include_router(api_router)

        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.ws_manager.websocket_endpoint(websocket)

    def start(self):
        """Start the web server"""
        if self.running:
            return False

        self.running = True

        # When using FastAPI with asyncio, create a loop for the WebSocketManager
        # and integrate it with the FastAPI app's event handlers
        @self.app.on_event("startup")
        async def startup_event():
            self.ws_manager.running = True
            self._update_task = asyncio.create_task(self.ws_manager.update_loop())

        @self.app.on_event("shutdown")
        async def shutdown_event():
            if hasattr(self, "ws_manager"):
                await self.ws_manager.stop()

        # Start the server in a separate thread
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()
        return True

    def _run_server(self):
        """Run the uvicorn server with optimized settings"""
        import uvicorn

        # Use optimized server settings for Raspberry Pi
        uvicorn.run(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="error",  # Minimal logging
            loop="asyncio",
            workers=1,  # Single worker to reduce memory usage
            limit_concurrency=20,  # Limit concurrent connections
            timeout_keep_alive=5,  # Reduce keep-alive timeout
        )

    def stop(self):
        """Stop the web server"""
        if not self.running:
            return

        self.running = False

        # Stop websocket manager
        if hasattr(self, "ws_manager"):
            self.ws_manager.stop()

        # Allow time for graceful shutdown
        time.sleep(0.1)

        logger.info("Web server stopped")

    def cleanup(self):
        """Clean up resources before shutdown"""
        if hasattr(self, "websocket_manager"):
            self.websocket_manager.stop()
        # ...any other existing cleanup code...
