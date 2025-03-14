from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import time
import threading
import logging
from typing import List, Dict, Any, Optional

# Import API components
from .api.routes import router as api_router, EmotionLightingAPI
from .api.websocket import WebSocketManager

# Establish a logger with reduced logging level for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("emotion_lighting")


class EmotionWebServer:
    """Web server for the Emotion Lighting system using FastAPI"""

    def __init__(
        self,
        emotion_tracker,
        touch_tracker,
        database,
        host="0.0.0.0",
        port=8000,
    ):
        """Initialize the web server

        Args:
            emotion_tracker: EmotionTracker instance
            touch_tracker: TouchTracker instance
            database: Database instance
            host: Host to bind the server to
            port: Port to run the server on
        """
        self.emotion_tracker = emotion_tracker
        self.touch_tracker = touch_tracker
        self.database = database
        self.host = host
        self.port = port

        # State management
        self.running = False
        self.lock = threading.Lock()

        # Create FastAPI app
        self.app = FastAPI(
            title="Emotion Lighting System",
            description="Control and monitor the emotion lighting system",
            version="1.0.0",
        )

        # Configure CORS to allow frontend connections
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # For development - restrict in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Initialize WebSocket manager
        self.ws_manager = WebSocketManager(emotion_tracker, touch_tracker, database)

        # Initialize API routes
        self.api = EmotionLightingAPI(emotion_tracker, touch_tracker, database)

        # Set up routes
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes and WebSocket endpoint"""

        # Mount static files directory
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        if os.path.exists(static_dir):
            self.app.mount("/static", StaticFiles(directory=static_dir), name="static")

        # Index route
        @self.app.get("/", response_class=HTMLResponse)
        async def get_index():
            """Serve the index.html file"""
            html_path = os.path.join(static_dir, "index.html")
            if os.path.exists(html_path):
                with open(html_path, "r") as f:
                    return f.read()
            return """
            <html>
                <head><title>Emotion Lighting System</title></head>
                <body>
                    <h1>Emotion Lighting System</h1>
                    <p>Web interface is being set up.</p>
                </body>
            </html>
            """

        # Include API routes
        self.app.include_router(api_router)

        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.ws_manager.websocket_endpoint(websocket)

    async def _update_loop(self):
        """Background task for updating connected clients"""
        while self.running:
            try:
                # Let the WebSocket manager handle updates
                await asyncio.sleep(0.25)  # Just keep the loop running
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(1)  # Back off on error

    def start(self):
        """Start the web server"""
        if self.running:
            return

        self.running = True

        # Start WebSocket manager
        self.ws_manager.start()

        # Create asyncio task for the update loop
        loop = asyncio.get_event_loop()
        self.update_task = loop.create_task(self.ws_manager.update_loop())

        # Import here to avoid circular imports
        import uvicorn

        # Start the server in a thread
        self.thread = threading.Thread(
            target=uvicorn.run,
            kwargs={
                "app": self.app,
                "host": self.host,
                "port": self.port,
                "log_level": "warning",  # Reduce logging for Raspberry Pi
                "loop": "asyncio",
            },
            daemon=True,
        )
        self.thread.start()

        logger.info(f"Web server started on http://{self.host}:{self.port}")

    def stop(self):
        """Stop the web server"""
        self.running = False

        # Stop WebSocket manager
        self.ws_manager.stop()

        # Give the update loop time to exit gracefully
        time.sleep(0.5)

        logger.info("Web server stopped")
