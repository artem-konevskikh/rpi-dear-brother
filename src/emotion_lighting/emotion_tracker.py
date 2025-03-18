import cv2
import time
import threading
from collections import deque
from fer import FER
import numpy as np
import logging

# Get logger for this module
logger = logging.getLogger("emotion_lighting.emotion_tracker")


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
        self.current_emotion = "no_face"
        self.emotion_start_time = 0
        self.emotion_confidence = 0.0

        # Emotion stability (prevents flickering)
        self.emotion_history = deque(maxlen=10)  # Increased history length
        self.emotion_confidence_history = {}  # Track confidence per emotion

        # Enhanced emotion stability parameters
        self.emotion_change_threshold = (
            0.2  # Slightly reduced threshold for easier changes
        )
        self.min_emotion_duration = 1.0  # Minimum time before allowing emotion change
        self.max_emotion_duration = 5.0  # Maximum time before forcing an emotion update
        self.last_emotion_change_time = 0

        # Thread management
        self.thread = None
        self.lock = threading.Lock()

        # Performance optimizations
        self.frame_width = 640  # Reduced resolution
        self.frame_height = 480  # Reduced resolution
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
            logger.error(f"Could not open webcam with ID {self.camera_id}")
            self.running = False
            return

        last_detection_time = 0
        consecutive_no_face_frames = 0
        no_face_threshold = 5  # Number of consecutive frames with no face before changing state

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
                        consecutive_no_face_frames = 0  # Reset counter when face is detected
                    else:
                        # No face detected
                        consecutive_no_face_frames += 1
                        if consecutive_no_face_frames >= no_face_threshold:
                            # Set to no_face state after several consecutive frames with no face
                            self._handle_no_face_detected()

                    last_detection_time = current_time

                # Sleep to reduce CPU usage - longer interval
                time.sleep(0.03)

        except Exception as e:
            logger.error(f"Error in tracking loop: {e}")
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
            # Ensure frame is RGB (critical for accurate emotion detection)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect emotions with minimum face size requirements
            result = self.detector.detect_emotions(rgb_frame)

            if not result:
                return None

            # Get the first face and validate its detection
            face = result[0]
            face_box = face["box"]
            face_width = face_box[2]
            face_height = face_box[3]
            
            # Filter out small faces (likely false detections)
            min_face_size = min(self.frame_width, self.frame_height) * 0.1  # Face should be at least 10% of frame
            if face_width < min_face_size or face_height < min_face_size:
                return None

            emotions = face["emotions"]

            # Find dominant emotion faster using numpy
            emotion_names = list(emotions.keys())
            emotion_values = np.array(list(emotions.values()))
            dominant_idx = np.argmax(emotion_values)

            dominant_emotion = emotion_names[dominant_idx]
            confidence = emotion_values[dominant_idx]

            # Include all emotion scores for better decision-making
            return {
                "emotion": dominant_emotion,
                "confidence": confidence,
                "all_scores": emotions,
            }

        except Exception as e:
            logger.error(f"Error detecting emotions: {e}")
            return None

    def _process_emotion(self, emotion_data):
        """Process detected emotion with enhanced stability

        Args:
            emotion_data: Dict with emotion and confidence
        """
        try:
            # Extract current detected emotion (raw data)
            emotion = emotion_data["emotion"]
            confidence = emotion_data["confidence"]
            all_scores = emotion_data.get("all_scores", {})

            # Check if current detection is particularly strong - might want to use this directly
            very_confident_detection = (
                confidence > 0.7
            )  # Use high confidence detections immediately

            # Add to history for stability
            self.emotion_history.append(emotion)

            # Update all detected emotions' confidence scores
            for em, conf in all_scores.items():
                if em not in self.emotion_confidence_history:
                    self.emotion_confidence_history[em] = []
                self.emotion_confidence_history[em] = self.emotion_confidence_history[em][
                    -4:
                ] + [conf]

            # Calculate weighted scores for each emotion
            emotion_scores = {}
            for em, confs in self.emotion_confidence_history.items():
                # Count occurrences in history (frequency component)
                frequency = sum(1 for e in self.emotion_history if e == em)

                # Calculate average confidence (strength component)
                avg_confidence = sum(confs) / len(confs) if confs else 0

                # Combined score: frequency * average confidence
                emotion_scores[em] = (
                    frequency / len(self.emotion_history)
                ) * avg_confidence

            # Find the emotion with the highest score
            if emotion_scores:
                stable_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
                stable_confidence = max(
                    self.emotion_confidence_history.get(stable_emotion, [0])
                )
            else:
                stable_emotion = "neutral"
                stable_confidence = 0.0

            current_time = time.time()

            with self.lock:
                # Calculate time since last emotion change
                time_since_last_change = current_time - self.last_emotion_change_time

                # Determine if we should force an update
                force_update = time_since_last_change > self.max_emotion_duration or (
                    very_confident_detection and emotion != self.current_emotion
                )

                # Normal update conditions
                emotion_change_allowed = time_since_last_change > self.min_emotion_duration

                significant_change = (
                    stable_emotion != self.current_emotion
                    and emotion_scores.get(stable_emotion, 0)
                    > emotion_scores.get(self.current_emotion, 0)
                    + self.emotion_change_threshold
                )

                # Allow update if conditions are met or if we need to force an update
                if (significant_change and emotion_change_allowed) or force_update:
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
                    self.emotion_confidence = stable_confidence
                    self.emotion_start_time = current_time
                    self.last_emotion_change_time = current_time

                    # Update LED color based on emotion
                    self.led_controller.set_emotion_color(stable_emotion)
        except Exception as e:
            logger.error(f"Error processing emotion: {e}")

    def _log_emotion(self, emotion, confidence, duration):
        """Log emotion data in a separate thread to prevent blocking"""
        try:
            self.database.log_emotion(emotion, confidence, duration)
            self.database.update_daily_stats()
        except Exception as e:
            logger.error(f"Error logging emotion: {e}")
            
    def _handle_no_face_detected(self):
        """Handle the case when no face is detected in the frame"""
        try:
            with self.lock:
                # Only change state if we're not already in no_face state
                if self.current_emotion != "no_face":
                    # Log the duration of the previous emotion if it wasn't the first one
                    if self.emotion_start_time > 0:
                        duration = time.time() - self.emotion_start_time
                        # Log emotion asynchronously to prevent blocking
                        threading.Thread(
                            target=self._log_emotion,
                            args=(self.current_emotion, self.emotion_confidence, duration),
                        ).start()
                    
                    # Update to no_face state
                    self.current_emotion = "no_face"
                    self.emotion_confidence = 0.0
                    self.emotion_start_time = time.time()
                    self.last_emotion_change_time = time.time()
                    
                    # Update LED color for no_face state
                    self.led_controller.set_emotion_color("no_face")
        except Exception as e:
            logger.error(f"Error handling no face detection: {e}")
