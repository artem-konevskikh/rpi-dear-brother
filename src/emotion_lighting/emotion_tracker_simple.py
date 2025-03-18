import cv2
import time
import threading
from fer import FER
import logging

# Get logger for this module
logger = logging.getLogger("emotion_lighting.emotion_tracker")


class EmotionTracker:
    """Track facial emotions from a webcam feed - simplified version without stability mechanisms"""

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

        # Thread management
        self.thread = None
        self.lock = threading.Lock()

        # Performance optimizations
        self.frame_width = 640  # Reduced resolution
        self.frame_height = 480  # Reduced resolution
        self.process_every_n_frames = 2  # Process more frames for faster response
        self.frame_counter = 0
        self.min_detection_interval = 0.1  # Detect emotions more frequently

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
        no_face_threshold = 2  # Reduced threshold for faster no_face detection

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
                        # Process detected emotion - directly update without stability checks
                        self._process_emotion(emotion_data)
                        consecutive_no_face_frames = 0  # Reset counter when face is detected
                    else:
                        # No face detected
                        consecutive_no_face_frames += 1
                        if consecutive_no_face_frames >= no_face_threshold:
                            # Set to no_face state immediately after threshold
                            self._handle_no_face_detected()

                    last_detection_time = current_time

                # Sleep to reduce CPU usage - minimal interval for faster response
                time.sleep(0.01)

        except Exception as e:
            logger.error(f"Error in tracking loop: {e}")
        finally:
            # Clean up
            cap.release()

    def _detect_emotions(self, frame):
        """Detect emotions in a frame - basic implementation

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
            min_face_size = min(self.frame_width, self.frame_height) * 0.15  # Face should be at least 15% of frame
            if face_width < min_face_size or face_height < min_face_size:
                return None

            emotions = face["emotions"]

            # Find dominant emotion with confidence threshold
            dominant_emotion, confidence = max(emotions.items(), key=lambda x: x[1])
            
            # Only return emotion if confidence is high enough
            if confidence < 0.6:  # Increased confidence threshold
                return None
                
            return {"emotion": dominant_emotion, "confidence": confidence}

        except Exception as e:
            logger.error(f"Error detecting emotions: {e}")
            return None

    def _process_emotion(self, emotion_data):
        """Process detected emotion - simplified without stability mechanisms

        Args:
            emotion_data: Dict with emotion and confidence
        """
        try:
            # Extract current detected emotion (raw data)
            emotion = emotion_data["emotion"]
            confidence = emotion_data["confidence"]

            current_time = time.time()

            with self.lock:
                # Log the previous emotion if:
                if emotion != self.current_emotion and self.emotion_start_time > 0:
                    duration = current_time - self.emotion_start_time
                    # Log emotion asynchronously to prevent blocking
                    self._log_emotion(self.current_emotion, self.emotion_confidence, duration)

                # Update to the new emotion immediately
                self.current_emotion = emotion
                self.emotion_confidence = confidence
                self.emotion_start_time = current_time

                # Update LED color based on emotion immediately
                self.led_controller.set_emotion_color(emotion)

        except Exception as e:
            logger.error(f"Error processing emotion: {e}")

    def _log_emotion(self, emotion, confidence, duration):
        """Log emotion data in a separate thread to prevent blocking"""
        def _log_task():
            try:
                self.database.log_emotion(emotion, confidence, duration)
                self.database.update_daily_stats()
            except Exception as e:
                logger.error(f"Error logging emotion: {e}")
        
        # Create and start thread for logging
        thread = threading.Thread(target=_log_task)
        thread.daemon = True
        thread.start()

    def _handle_no_face_detected(self):
        """Handle the case when no face is detected in the frame"""
        try:
            with self.lock:
                # Only change state if we're not already in no_face state
                if self.current_emotion != "no_face":
                    # Log the duration of the previous emotion only if it was a real emotion
                    if self.emotion_start_time > 0 and self.current_emotion != "no_face":
                        duration = time.time() - self.emotion_start_time
                        # Log emotion asynchronously to prevent blocking
                        self._log_emotion(self.current_emotion, self.emotion_confidence, duration)

                    # Update to no_face state without logging it
                    self.current_emotion = "no_face"
                    self.emotion_confidence = 0.0
                    self.emotion_start_time = 0  # Reset start time for no_face state

                    # Update LED color for no_face state
                    self.led_controller.set_emotion_color("no_face")
        except Exception as e:
            logger.error(f"Error handling no face detection: {e}")
