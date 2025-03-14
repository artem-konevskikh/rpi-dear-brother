import cv2
import time
import threading
from collections import deque
from fer import FER
import numpy as np


class EmotionTracker:
    """Track facial emotions from a webcam feed - optimized for Raspberry Pi"""

    def __init__(self, database, led_controller, camera_id=0):
        """Initialize the emotion tracker

        Args:
            database: Database instance for logging emotion data
            led_controller: LED controller for changing colors based on emotions
            camera_id: Camera device ID
        """
        self.database = database
        self.led_controller = led_controller
        self.camera_id = camera_id

        # Initialize emotion detector (load only once)
        self.detector = FER()

        # State tracking
        self.running = False
        self.current_emotion = "neutral"
        self.emotion_start_time = 0
        self.emotion_confidence = 0.0

        # Emotion stability (prevents flickering)
        self.emotion_history = deque(maxlen=5)

        # Thread management
        self.thread = None
        self.lock = threading.Lock()

        # Performance optimizations
        self.frame_width = 320  # Reduced resolution
        self.frame_height = 240  # Reduced resolution
        self.process_every_n_frames = 5  # Skip frames
        self.frame_counter = 0
        self.min_detection_interval = 0.5  # Detect emotions every 0.5 seconds

        # Face detection cache
        self.last_face_position = None
        self.face_ttl = 3  # Number of frames to keep the face position

    def start(self):
        """Start emotion tracking"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._tracking_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop emotion tracking"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)

    def get_current_emotion(self):
        """Get the current detected emotion

        Returns:
            tuple: (emotion, confidence)
        """
        with self.lock:
            return (self.current_emotion, self.emotion_confidence)

    def _tracking_loop(self):
        """Main emotion tracking loop"""
        # Initialize webcam with lower resolution
        cap = cv2.VideoCapture(self.camera_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

        # Set buffer size to minimum to reduce latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            print(f"Error: Could not open webcam with ID {self.camera_id}")
            self.running = False
            return

        last_detection_time = 0

        try:
            while self.running:
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)  # Wait and retry if frame couldn't be read
                    continue

                self.frame_counter += 1

                # Process emotions at reduced framerate
                current_time = time.time()
                if (
                    self.frame_counter % self.process_every_n_frames == 0
                    and current_time - last_detection_time > self.min_detection_interval
                ):
                    # Resize frame for faster processing if needed
                    if (
                        frame.shape[0] > self.frame_height
                        or frame.shape[1] > self.frame_width
                    ):
                        frame = cv2.resize(frame, (self.frame_width, self.frame_height))

                    # Detect emotions
                    emotion_data = self._detect_emotions(frame)
                    if emotion_data:
                        # Process detected emotion
                        self._process_emotion(emotion_data)

                    last_detection_time = current_time

                # Sleep to reduce CPU usage - longer interval
                time.sleep(0.03)

        except Exception as e:
            print(f"Error in tracking loop: {e}")
        finally:
            # Clean up
            cap.release()

    def _detect_emotions(self, frame):
        """Detect emotions in a frame - optimized

        Args:
            frame: OpenCV image frame

        Returns:
            dict with emotion and confidence, or None if no face detected
        """
        try:
            # Convert frame to RGB for FER
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect emotions
            result = self.detector.detect_emotions(rgb_frame)

            if not result:
                return None

            # Get the dominant emotion from the first face
            face = result[0]
            emotions = face["emotions"]

            # Find dominant emotion faster using numpy
            emotion_names = list(emotions.keys())
            emotion_values = np.array(list(emotions.values()))
            dominant_idx = np.argmax(emotion_values)

            dominant_emotion = emotion_names[dominant_idx]
            confidence = emotion_values[dominant_idx]

            return {"emotion": dominant_emotion, "confidence": confidence}

        except Exception as e:
            print(f"Error detecting emotions: {e}")
            return None

    def _process_emotion(self, emotion_data):
        """Process detected emotion

        Args:
            emotion_data: Dict with emotion and confidence
        """
        # Add to history for stability
        self.emotion_history.append(emotion_data["emotion"])

        # Use Counter-like approach for faster counting
        counts = {}
        for emotion in self.emotion_history:
            counts[emotion] = counts.get(emotion, 0) + 1

        # Get the most frequent emotion in history
        stable_emotion = max(counts.items(), key=lambda x: x[1])[0]

        with self.lock:
            current_time = time.time()

            # If emotion has changed, log the previous one and start tracking the new one
            if stable_emotion != self.current_emotion:
                # Log the duration of the previous emotion if it wasn't the first one
                if self.emotion_start_time > 0:
                    duration = current_time - self.emotion_start_time
                    # Log emotion asynchronously to prevent blocking
                    threading.Thread(
                        target=self._log_emotion,
                        args=(self.current_emotion, self.emotion_confidence, duration),
                    ).start()

                # Update to the new emotion
                self.current_emotion = stable_emotion
                self.emotion_confidence = emotion_data["confidence"]
                self.emotion_start_time = current_time

                # Update LED color based on emotion
                self.led_controller.set_emotion_color(stable_emotion)

    def _log_emotion(self, emotion, confidence, duration):
        """Log emotion data in a separate thread to prevent blocking"""
        try:
            self.database.log_emotion(emotion, confidence, duration)
            self.database.update_daily_stats()
        except Exception as e:
            print(f"Error logging emotion: {e}")
