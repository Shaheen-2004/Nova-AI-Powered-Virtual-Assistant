"""
NOVA - Intelligent Vision Assistant
Main entry point for the application.
"""

import sys
import os
import subprocess

# Auto-restart with venv if not already using it
venv_python = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "python.exe")
if os.path.exists(venv_python) and sys.executable.lower() != venv_python.lower() and "venv" not in sys.executable.lower():
    print(f"DEBUG: Not using venv. Restarting with: {venv_python}")
    result = subprocess.run([venv_python] + sys.argv)
    sys.exit(result.returncode)

print(f"DEBUG: Running with Python: {sys.executable}")
print(f"DEBUG: Python Path: {sys.path[:3]}")

import cv2
import numpy as np
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
    from PyQt6.QtGui import QImage, QPixmap
except ImportError:
    print("\n" + "="*60)
    print("ERROR: PyQt6 not found!")
    print("Please run NOVA using the 'run.bat' file or activate the venv:")
    print("1. Double-click 'run.bat'")
    print("2. Or run: .\\venv\\Scripts\\python.exe main.py")
    print("="*60 + "\n")
    sys.exit(1)

from ui.main_window import MainWindow
from ui.arc_reactor import ArcReactor
from core.speech_handler import SpeechHandler
from core.ai_brain import AIBrain
from core.intent_parser import IntentParser, Intent
from vision.object_detection import ObjectDetector
from vision.gesture_recognition import GestureRecognizer, Gesture
from vision.hand_sign_recognizer import ASLRecognizer
from vision.air_drawing.drawing_engine import AirDrawingEngine
from control.system_commands import SystemCommands
from control.app_launcher import AppLauncher
from utils.logger import setup_logger, get_logger
from utils.config import Config

# Setup logging
logger = setup_logger(__name__, log_file='logs/nova.log')

def exception_hook(exctype, value, traceback):
    logger.error("Unhandled exception:", exc_info=(exctype, value, traceback))
    sys.__excepthook__(exctype, value, traceback)

sys.excepthook = exception_hook


class CameraThread(QThread):
    """Thread for camera processing."""
    
    frame_ready = pyqtSignal(np.ndarray)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.camera = None
    
    def run(self):
        """Run camera capture loop."""
        self.camera = cv2.VideoCapture(0)
        self.running = True
        
        while self.running:
            ret, frame = self.camera.read()
            if ret:
                self.frame_ready.emit(frame)
            self.msleep(33)  # ~30 FPS
    
    def stop(self):
        """Stop camera thread."""
        self.running = False
        if self.camera:
            self.camera.release()


class NovaApp:
    """Main NOVA application controller."""
    
    def __init__(self):
        """Initialize NOVA application."""
        # Initialize components as None to avoid AttributeErrors
        self.speech_handler = None
        self.ai_brain = None
        self.intent_parser = None
        self.object_detector = None
        self.gesture_recognizer = None
        self.system_commands = None
        self.app_launcher = None
        self.camera_thread = None
        
        logger.info("=" * 60)
        logger.info("NOVA - Intelligent Vision Assistant")
        logger.info("=" * 60)
        
        # Load configuration
        self.config = Config()
        
        # Initialize Qt application
        self.qt_app = QApplication(sys.argv)
        self.window = MainWindow()
        
        # Initialize components
        logger.info("Initializing components...")
        try:
            self.speech_handler = SpeechHandler()
            logger.info("[V] SpeechHandler initialized")
            
            self.ai_brain = AIBrain()
            logger.info("[V] AIBrain initialized")
            
            self.intent_parser = IntentParser()
            logger.info("[V] IntentParser initialized")
            
            self.object_detector = ObjectDetector()
            logger.info("[V] ObjectDetector initialized")
            
            self.gesture_recognizer = GestureRecognizer()
            logger.info("[V] GestureRecognizer initialized")
            
            self.system_commands = SystemCommands()
            logger.info("[V] SystemCommands initialized")
            
            self.app_launcher = AppLauncher()
            logger.info("[V] AppLauncher initialized")
            
            self.asl_recognizer = ASLRecognizer()
            logger.info("[V] ASLRecognizer initialized")
            
            self.drawing_engine = AirDrawingEngine()
            logger.info("[V] AirDrawingEngine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}", exc_info=True)
            raise
        
        # Camera thread
        try:
            self.camera_thread = CameraThread()
            self.camera_thread.frame_ready.connect(self.process_frame)
            logger.info("[V] CameraThread initialized")
        except Exception as e:
            logger.error(f"Failed to initialize CameraThread: {e}", exc_info=True)
            raise
        
        # State
        self.current_frame = None
        self.latest_detections = []
        self.is_listening = False
        self.frame_count = 0
        self.detection_interval = 6 # Run detection every 6 frames (~5 FPS)
        
        if self.camera_thread:
            # Setup UI connections - only after components are ready
            self.setup_connections()
            self.window.listen_requested.connect(self.start_listening)
            
        # Show greeting
        try:
            greeting = self.ai_brain.get_greeting()
            self.window.add_transcript_message("nova", greeting)
            if self.speech_handler:
                self.speech_handler.speak(greeting, blocking=False)
        except Exception as e:
            logger.warning(f"Failed to show greeting: {e}")
            
        logger.info("NOVA initialized successfully!")
    
    def setup_connections(self):
        """Set up signal/slot connections."""
        # Start camera
        self.camera_thread.start()
        
        # Setup listening timer (backup check)
        self.listen_timer = QTimer()
        self.listen_timer.timeout.connect(self.check_for_input)
        self.listen_timer.start(10000)  # Check every 10 seconds
    
    def process_frame(self, frame: np.ndarray):
        """
        Process camera frame with vision systems.
        
        Args:
            frame: Camera frame
        """
        self.current_frame = frame.copy()
        
        # Object detection (Skip frames to reduce lag)
        if self.frame_count % self.detection_interval == 0:
            detections = self.object_detector.detect(frame)
            self.latest_detections = detections
            
            # Arc Reactor state based on objects
            if detections and self.window.arc_reactor.state == ArcReactor.IDLE:
                self.window.arc_reactor.set_state(ArcReactor.VISION)
            elif not detections and self.window.arc_reactor.state == ArcReactor.VISION:
                self.window.arc_reactor.set_state(ArcReactor.IDLE)
        else:
            detections = self.latest_detections
            
        frame = self.object_detector.draw_detections(frame, detections)
        
        # Gesture recognition (Keep at high frequency for responsiveness)
        gesture, frame = self.gesture_recognizer.process_frame(frame)
        
        if gesture:
            self.handle_gesture(gesture)
            
        # ASL / Sign Language Recognition
        if self.gesture_recognizer.last_landmarks:
            lmList = self.gesture_recognizer.last_landmarks.get("lmList", [])
            letter, confidence = self.asl_recognizer.process_landmarks(lmList, frame.shape[:2])
            if letter:
                self.window.current_letter_label.setText(f"Letter: {letter} ({int(confidence*100)}%)")
            else:
                self.window.current_letter_label.setText("Letter: -")
        else:
            self.window.current_letter_label.setText("Letter: -")
            
        current_word = self.asl_recognizer.get_word()
        if current_word:
            self.window.current_word_label.setText(f"Spelling: {current_word}")
        else:
            self.window.current_word_label.setText("Spelling: ")
            
        if self.asl_recognizer.word_ready:
            self.asl_recognizer.word_ready = False
            full_word = self.asl_recognizer.get_word()
            self.asl_recognizer.reset_word()
            
            # Process the signed word/command
            self.handle_voice_input(full_word)
            
        # Air Drawing
        if self.drawing_engine.active:
            # Need hand landmarks from gesture_recognizer results if possible
            # For now, we'll re-run or better, extract from gesture recognizer
            if hasattr(self.gesture_recognizer, 'last_landmarks') and self.gesture_recognizer.last_landmarks:
                point = self.drawing_engine.process_hand_data(self.gesture_recognizer.last_landmarks, frame.shape[:2])
                if point:
                    self.drawing_engine.draw(point, is_fist=(gesture == Gesture.FIST))
            
            frame = self.drawing_engine.get_overlay(frame)
        
        self.frame_count += 1
        
        # Convert frame to QPixmap and display
        self.display_frame(frame)
    
    def display_frame(self, frame: np.ndarray):
        """Display frame in UI."""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        
        # Optimize QImage creation
        qt_image = QImage(rgb_frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        
        # Use FastTransformation for smoother real-time playback
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.window.camera_display.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        self.window.camera_display.setPixmap(scaled_pixmap)
    
    def handle_gesture(self, gesture: Gesture):
        """
        Handle detected gesture.
        
        Args:
            gesture: Detected gesture
        """
        gesture_name = self.gesture_recognizer.get_gesture_name(gesture)
        logger.info(f"Gesture detected: {gesture_name}")
        
        # Arc Reactor State
        self.window.arc_reactor.set_state(ArcReactor.GESTURE)
        QTimer.singleShot(500, lambda: self.window.arc_reactor.set_state(ArcReactor.IDLE))
        
        if gesture == Gesture.OPEN_PALM:
            if self.drawing_engine.active:
                self.drawing_engine.active = False
                self.speech_handler.speak("Exiting drawing mode.", blocking=False)
            else:
                # Activate listening
                self.start_listening()
        
        elif gesture == Gesture.SWIPE_LEFT:
            if self.drawing_engine.active:
                self.drawing_engine.next_color()
                self.speech_handler.speak("Color changed.", blocking=False)
            else:
                self.handle_voice_input("volume down")
                
        elif gesture == Gesture.SWIPE_RIGHT:
            if self.drawing_engine.active:
                 self.drawing_engine.next_color()
                 self.speech_handler.speak("Color changed.", blocking=False)
            else:
                self.handle_voice_input("volume up")
                
        elif gesture == Gesture.FIST:
            if not self.drawing_engine.active:
                # Stop speaking
                if self.speech_handler:
                    self.speech_handler.stop_speaking()
                self.window.update_status('audio', False)
            
        elif gesture in [Gesture.POINT_UP, Gesture.PEACE_SIGN]:
            if not self.drawing_engine.active:
                self.drawing_engine.active = True
                self.drawing_engine.reset_canvas()
                self.speech_handler.speak("Air drawing mode activated. Use your index finger to draw, or fist to lift the pen.", blocking=False)
                
        elif gesture == Gesture.POINT_DOWN:
            if self.drawing_engine.active:
                self.drawing_engine.reset_canvas()
                self.speech_handler.speak("Canvas cleared.", blocking=False)
            else:
                self.handle_voice_input("mute")
    
    def check_for_input(self):
        """Check for voice input (simulates wake word)."""
        if not hasattr(self, 'speech_handler') or not self.speech_handler:
            return
            
        if not self.is_listening and not self.speech_handler.is_speaking:
            # Since hand gestures are disabled, we automatically start listening
            self.start_listening()
    
    def start_listening(self):
        """Start listening for voice input."""
        if not self.speech_handler or self.is_listening or self.speech_handler.is_speaking:
            return
        
        self.is_listening = True
        self.window.update_status('mic', True)
        self.window.listen_button.setEnabled(False)
        self.window.listen_button.setText("LISTENING...")
        
        # Arc Reactor State
        self.window.arc_reactor.set_state(ArcReactor.LISTENING)
        
        logger.info("Listening for voice input...")
        # Visual feedback in transcript
        self.window.add_transcript_message("system", "NOVA is listening...")
        
        # Listen in background
        def on_speech_result(text):
            self.is_listening = False
            self.window.update_status('mic', False)
            self.window.listen_button.setEnabled(True)
            self.window.listen_button.setText("🎤 LISTEN")
            
            if text:
                # Arc Reactor State
                self.window.arc_reactor.set_state(ArcReactor.PROCESSING)
                self.handle_voice_input(text)
            else:
                # Arc Reactor State back to idle
                self.window.arc_reactor.set_state(ArcReactor.IDLE)
                self.window.add_transcript_message("system", "No speech detected.")
        
        self.speech_handler.listen_async(on_speech_result)
    
    def handle_voice_input(self, text: str):
        """
        Handle voice input from user.
        
        Args:
            text: Recognized speech text
        """
        logger.info(f"User said: {text}")
        self.window.add_transcript_message("user", text)
        
        # Parse intent
        intent = self.intent_parser.parse(text)
        
        # Handle based on intent
        response = self.process_intent(intent, text)
        
        # Display and speak response
        self.window.add_transcript_message("nova", response)
        self.window.update_status('audio', True)
        self.window.arc_reactor.set_state(ArcReactor.SPEAKING)
        if hasattr(self, 'speech_handler') and self.speech_handler:
            self.speech_handler.speak(response, blocking=False)
        
        # Reset audio status after speaking
        def reset_state():
            self.window.update_status('audio', False)
            self.window.arc_reactor.set_state(ArcReactor.IDLE)
            
        QTimer.singleShot(len(response) * 60, reset_state)
        
        # CONTINUOUS CONVERSATION:
        # After a short delay (approx when speech ends), try to listen again
        # This makes it feel like an actual conversation loop
        speech_duration = max(2000, len(response) * 60) # Estimate duration
        QTimer.singleShot(speech_duration + 500, self.start_listening)
    
    def process_intent(self, intent: Intent, original_text: str) -> str:
        """
        Process user intent and generate response.
        
        Args:
            intent: Parsed intent
            original_text: Original user text
        
        Returns:
            Response text
        """
        self.window.update_status('ai', True)
        
        try:
            # Handle Application Launching (including YouTube, Brave, etc.)
            if intent.type == Intent.APP_LAUNCH:
                response = self.app_launcher.launch(intent.data['app_name'])
            
            # Handle Web Search requests
            elif intent.type == Intent.WEB_SEARCH:
                response = self.system_commands.web_search(intent.data['query'])
            
            # Handle Vision Queries (What do you see?)
            elif intent.type == Intent.VISION_QUERY:
                description = self.object_detector.get_description(self.latest_detections)
                response = description
            
            # Handle Time and Date queries
            elif intent.type == Intent.TIME_QUERY:
                response = self.system_commands.get_time()
            
            # Media control access logic (Volume, Play/Pause)
            elif intent.type == Intent.MEDIA_CONTROL:
                action = intent.data['action']
                if 'volume up' in action:
                    response = self.system_commands.volume_up()
                elif 'volume down' in action:
                    response = self.system_commands.volume_down()
                elif 'mute' in action:
                    response = self.system_commands.mute()
                else:
                    response = f"Media control '{action}' not yet implemented"
            
            elif intent.type == Intent.POWER_MODE:
                action = intent.data.get('action', 'get')
                if action == 'get':
                    response = self.system_commands.get_power_mode()
                else:
                    mode = intent.data.get('mode', '')
                    response = self.system_commands.set_power_mode(mode)
            
            elif intent.type == Intent.SYSTEM_COMMAND:
                response = self.system_commands.execute_command(intent.data['command'])
            
            # Handle Keyboard Access / Automatic Typing
            elif intent.type == Intent.TYPING_COMMAND:
                text_to_type = intent.data.get('text', '')
                if text_to_type:
                    # Provide immediate feedback so user knows it's starting
                    self.speech_handler.speak("Understood. I will start typing in two seconds. Please focus your cursor.", blocking=False)
                    response = self.system_commands.type_text(text_to_type)
                else:
                    response = "I heard you wanted me to type, but I didn't catch the text. Could you repeat it?"
            
            # Handle Air Drawing Control
            elif intent.type == Intent.DRAWING_CONTROL:
                if any(word in original_text for word in ["stop", "exit", "close"]):
                    self.drawing_engine.active = False
                    response = "Exiting air drawing mode."
                else:
                    self.drawing_engine.active = True
                    self.drawing_engine.reset_canvas()
                    response = "Air drawing mode activated. You can now draw on the screen with your index finger."
            
            else:
                # Conversation with AI
                response = self.ai_brain.chat(original_text)
        
        except Exception as e:
            logger.error(f"Error processing intent: {e}")
            response = "I encountered an issue processing that request."
        
        finally:
            self.window.update_status('ai', False)
        
        return response
    
    def run(self):
        """Run the application."""
        self.window.showMaximized()
        self.window.raise_()
        self.window.activateWindow()
        
        # Initial status
        self.window.update_status('vision', True)
        self.window.update_status('gestures', True)
        
        logger.info("NOVA is now running!")
        logger.info("Use Open Palm gesture to activate listening, or wait for periodic checks")
        
        sys.exit(self.qt_app.exec())
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Shutting down NOVA...")
        self.camera_thread.stop()
        self.camera_thread.wait()
        self.gesture_recognizer.cleanup()
        if self.speech_handler:
            self.speech_handler.cleanup()
        logger.info("NOVA shutdown complete")


def main():
    """Main entry point."""
    try:
        app = NovaApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        if 'app' in locals():
            app.cleanup()


if __name__ == "__main__":
    main()
