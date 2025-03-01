import cv2
import time
import threading
from collections import deque
from fer import FER


class EmotionTracker:
    """Track facial emotions from a webcam feed"""

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

        # Initialize emotion detector
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
        # Initialize webcam
        cap = cv2.VideoCapture(self.camera_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            print(f"Error: Could not open webcam with ID {self.camera_id}")
            self.running = False
            return

        last_detection_time = 0

        while self.running:
            # Read frame
            ret, frame = cap.read()
            if not ret:
                continue

            # Process emotions at reduced framerate (every 200ms)
            current_time = time.time()
            if current_time - last_detection_time > 0.2:
                # Detect emotions
                emotion_data = self._detect_emotions(frame)
                if emotion_data:
                    # Process detected emotion
                    self._process_emotion(emotion_data)

                last_detection_time = current_time

            # Sleep to reduce CPU usage
            time.sleep(0.01)

        # Clean up
        cap.release()

    def _detect_emotions(self, frame):
        """Detect emotions in a frame

        Args:
            frame: OpenCV image frame

        Returns:
            dict with emotion and confidence, or None if no face detected
        """
        # Convert frame to RGB for FER
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect emotions
        result = self.detector.detect_emotions(rgb_frame)

        if not result:
            return None

        # Get the dominant emotion from the first face
        face = result[0]
        emotions = face["emotions"]

        # Sort emotions by probability
        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        dominant_emotion = sorted_emotions[0][0]
        confidence = sorted_emotions[0][1]

        return {"emotion": dominant_emotion, "confidence": confidence}

    def _process_emotion(self, emotion_data):
        """Process detected emotion

        Args:
            emotion_data: Dict with emotion and confidence
        """
        # Add to history for stability
        self.emotion_history.append(emotion_data["emotion"])

        # Only update if the same emotion is detected consistently
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
                    self.database.log_emotion(
                        self.current_emotion, self.emotion_confidence, duration
                    )

                # Update to the new emotion
                self.current_emotion = stable_emotion
                self.emotion_confidence = emotion_data["confidence"]
                self.emotion_start_time = current_time

                # Update LED color based on emotion
                self.led_controller.set_emotion_color(stable_emotion)

                # Update daily stats in database
                self.database.update_daily_stats()
            else:
                # Just update confidence if same emotion
                self.emotion_confidence = emotion_data["confidence"]
