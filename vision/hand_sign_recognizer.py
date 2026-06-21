"""
Hand Sign Language (ASL) Recognition for NOVA.
Uses MediaPipe to track hand landmarks and a heuristic classifier for ASL letters.
"""

import cv2
import numpy as np
import time
import math
from typing import Optional, Tuple, List, Dict
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)

from typing import Optional, Tuple, List, Dict
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)

class ASLRecognizer:
    """Recognizes ASL alphabet letters and builds words."""
    
    def __init__(self):
        self.config = Config()
        self.enabled = self.config.get('vision.asl_recognition', True)
        
        # Recognition State
        self.current_word = ""
        self.current_letter = ""
        self.letter_hold_start = 0
        self.hold_time_threshold = 0.8  # Seconds to confirm a letter
        self.last_confirmed_letter = ""
        self.last_confirmation_time = 0
        self.cooldown = 1.5  # Seconds between same letter confirmations
        self.word_ready = False
        
        logger.info("ASL Recognizer initialized")

    def process_landmarks(self, lmList: List[List[int]], frame_shape: Tuple[int, int]) -> Tuple[Optional[str], float]:
        """
        Process landmarks detected by GestureRecognizer.
        lmList: [[x, y, z], ...] in pixel coordinates.
        Returns: (detected_letter, confidence)
        """
        if not self.enabled or not lmList:
            return None, 0.0
            
        # Classify letter
        detected_letter, confidence = self._classify_asl(lmList, frame_shape)
        
        # Logic for word building
        if detected_letter:
            self._update_word_logic(detected_letter)
                    
        return detected_letter, confidence

    def _update_word_logic(self, letter: str):
        """Handle letter confirmation and word building."""
        now = time.time()
        
        if letter == self.current_letter:
            if now - self.letter_hold_start >= self.hold_time_threshold:
                # Confirm letter if not too soon after last one of same type
                if letter != self.last_confirmed_letter or (now - self.last_confirmation_time > self.cooldown):
                    self.confirm_letter(letter)
                    self.last_confirmed_letter = letter
                    self.last_confirmation_time = now
        else:
            self.current_letter = letter
            self.letter_hold_start = now

    def confirm_letter(self, letter: str):
        """Add letter to current word or handle special gestures."""
        if letter == "SPACE":
            self.current_word += " "
        elif letter == "BACKSPACE":
            self.current_word = self.current_word[:-1]
        elif letter == "CLEAR":
            self.current_word = ""
        elif letter == "DONE":
            if self.current_word:
                self.word_ready = True
        else:
            self.current_word += letter
        logger.info(f"Confirmed ASL Letter: {letter}. Current word: {self.current_word}")

    def _classify_asl(self, lmList: List[List[int]], frame_shape: Tuple[int, int]) -> Tuple[Optional[str], float]:
        """ Geometric heuristic classifier for ASL alphabet. """
        # Normalize points to 0-1 range for consistency
        h, w = frame_shape
        points = []
        for p in lmList:
            points.append((p[0]/w, p[1]/h, p[2]))
        
        # Helper: Is finger up?
        # Tips: 8 (I), 12 (M), 16 (R), 20 (P)
        # MCPs: 5 (I), 9 (M), 13 (R), 17 (P)
        def is_up(tip, mcp): return points[tip][1] < points[mcp][1]
        
        index_up = is_up(8, 5)
        middle_up = is_up(12, 9)
        ring_up = is_up(16, 13)
        pinky_up = is_up(20, 17)
        
        # Thumb specific
        thumb_is_out = abs(points[4][0] - points[5][0]) > 0.05
        
        # Special Gestures / Core Letters
        
        # 1. Thumbs Up (DONE) - Hand closed, thumb pointing up
        if not index_up and not middle_up and not ring_up and not pinky_up:
            if points[4][1] < points[3][1] < points[2][1]:
                return "DONE", 0.95

        # 2. Thumbs Down (CLEAR) - Hand closed, thumb pointing down
        if not index_up and not middle_up and not ring_up and not pinky_up:
            if points[4][1] > points[3][1] > points[2][1]:
                return "CLEAR", 0.95

        # 3. L sign (L) - Index up, Thumb out
        if index_up and thumb_is_out and not middle_up and not ring_up and not pinky_up:
            return "L", 0.9
            
        # 4. Peace / V sign (V) - Index & Middle up, spread
        if index_up and middle_up and not ring_up and not pinky_up:
            return "V", 0.9
            
        # 5. OK / F sign (F) - Thumb and Index touch, others up
        dist_thumb_index = math.sqrt((points[4][0]-points[8][0])**2 + (points[4][1]-points[8][1])**2)
        if dist_thumb_index < 0.04 and middle_up and ring_up and pinky_up:
            return "F", 0.9
            
        # 6. Y sign (Y) - Thumb & Pinky out/up
        if thumb_is_out and pinky_up and not index_up and not middle_up and not ring_up:
            return "Y", 0.9
 
        # 7. I sign (I) - Pinky up only
        if pinky_up and not index_up and not middle_up and not ring_up and not thumb_is_out:
            return "I", 0.8
            
        # 8. B sign (B) - All fingers up and together
        if index_up and middle_up and ring_up and pinky_up:
            return "B", 0.8

        # 9. W sign (W) - Index, Middle, Ring up
        if index_up and middle_up and ring_up and not pinky_up:
            return "W", 0.85
            
        # 10. D sign (D) - Index up, others form circle/touch thumb
        if index_up and not middle_up and not ring_up and not pinky_up and not thumb_is_out:
            return "D", 0.8

        # 11. Pointing / G sign (G) - Index pointing sideways
        if index_up and not middle_up and not ring_up and not pinky_up:
             if abs(points[8][0] - points[5][0]) > 0.1: return "G", 0.7

        # 12. Fist / S sign (S) - All closed
        if not index_up and not middle_up and not ring_up and not pinky_up and not thumb_is_out:
            return "S", 0.7
            
        return None, 0.0

    def get_word(self) -> str:
        return self.current_word
        
    def reset_word(self):
        self.current_word = ""

    def cleanup(self):
        pass
