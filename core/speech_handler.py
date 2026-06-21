"""Speech handler for NOVA - Speech-to-Text and Text-to-Speech."""

import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
import winsound
from typing import Optional, Callable
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class SpeechHandler:
    """Handles speech recognition and text-to-speech synthesis."""
    
    def play_chime_start(self):
        """Play a high-pitched beep indicating listening has started."""
        try:
            winsound.Beep(1000, 150)  # Frequency, Duration
        except:
            pass

    def play_chime_stop(self):
        """Play a lower-pitched beep indicating listening has stopped."""
        try:
            winsound.Beep(600, 150)
        except:
            pass
    
    def __init__(self):
        """Initialize speech recognition and TTS engines."""
        self.config = Config()
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        try:
            # Adjust for ambient noise
            logger.info("Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            logger.error(f"Microphone calibration error: {e}")
        
        # TTS Engine properties
        self.tts_queue = queue.Queue()
        self.is_listening = False
        self.is_speaking = False
        self.stop_requested = False
        
        # Start dedicated TTS thread
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        logger.info("Speech handler initialized (TTS thread started)")
    
    def _tts_worker(self):
        """Dedicated thread worker for TTS using direct Windows SAPI."""
        import pythoncom
        import win32com.client
        
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Configure voice properties
            # Rate: -10 to 10
            rate = self.config.get('api.tts_voice_rate_sapi', 0)
            voice.Rate = rate
            
            # Volume: 0 to 100
            volume = self.config.get('api.tts_volume_sapi', 90)
            voice.Volume = volume
            
            # Prefer female voice if available
            voices = voice.GetVoices()
            for i in range(voices.Count):
                if "Zira" in voices.Item(i).GetDescription():
                    voice.Voice = voices.Item(i)
                    break
            
            while not self.stop_requested:
                try:
                    text = self.tts_queue.get(timeout=0.5)
                    if text:
                        self.is_speaking = True
                        logger.info(f"Speaking (SAPI): {text}")
                        # SVSFDefault = 0
                        voice.Speak(text)
                        self.is_speaking = False
                    self.tts_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"TTS Worker inner error (SAPI): {e}")
                    self.is_speaking = False
            
            pythoncom.CoUninitialize()
                        
        except Exception as e:
            logger.error(f"TTS Worker fatal error (SAPI): {e}")

    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Listen for speech and convert to text.
        
        Args:
            timeout: Seconds to wait for speech to start
            phrase_time_limit: Maximum seconds for phrase
        
        Returns:
            Recognized text or None if failed
        """
        self.is_listening = True
        
        try:
            with self.microphone as source:
                logger.info("Listening...")
                self.play_chime_start()  # Play sound
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                self.play_chime_stop()  # Stop sound
            
            logger.info("Processing speech...")
            
            # Use Google Speech Recognition (free)
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            
            return text
            
        except sr.WaitTimeoutError:
            logger.warning("Listening timeout - no speech detected")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during listening: {e}")
            return None
        finally:
            self.is_listening = False
    
    def speak(self, text: str, blocking: bool = False):
        """
        Add text to TTS queue for speaking.
        
        Args:
            text: Text to speak
            blocking: If True, wait for current speech to finish
        """
        if not text:
            return
            
        self.tts_queue.put(text)
        
        if blocking:
            self.tts_queue.join()
    
    def stop_speaking(self):
        """Clear current speech queue."""
        try:
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                    self.tts_queue.task_done()
                except queue.Empty:
                    break
            logger.info("Speech queue cleared")
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")
    
    def listen_async(self, callback: Callable[[Optional[str]], None]):
        """
        Listen for speech asynchronously and call callback with result.
        
        Args:
            callback: Function to call with recognized text
        """
        def _listen_thread():
            text = self.listen()
            callback(text)
        
        thread = threading.Thread(target=_listen_thread, daemon=True)
        thread.start()

    def cleanup(self):
        """Shutdown speech handler."""
        self.stop_requested = True
        self.stop_speaking()
