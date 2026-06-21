"""Hand gesture recognition using modern MediaPipe Tasks API."""

import cv2
import numpy as np
import time
import os
from typing import Optional, Tuple, List, Dict
from enum import Enum
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class Gesture(Enum):
    """Recognized hand gestures."""
    NONE = "none"
    OPEN_PALM = "open_palm"
    FIST = "fist"
    POINT_UP = "point_up"
    POINT_DOWN = "point_down"
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    PEACE_SIGN = "peace_sign"


class GestureRecognizer:
    """MediaPipe Tasks-based hand gesture recognizer."""
    
    def __init__(self):
        """Initialize Hand Landmarker."""
        self.config = Config()
        self.enabled = self.config.get('vision.gesture_recognition', True)
        
        # Path to model (should be in the same root as main.py)
        model_path = os.path.join(os.getcwd(), 'hand_landmarker.task')
        
        # MediaPipe Hand Landmarker Setup
        self.landmarker = None
        if self.enabled:
            if os.path.exists(model_path):
                try:
                    base_options = python.BaseOptions(model_asset_path=model_path)
                    options = vision.HandLandmarkerOptions(
                        base_options=base_options,
                        num_hands=1,
                        min_hand_detection_confidence=0.7,
                        min_hand_presence_confidence=0.7,
                        min_tracking_confidence=0.5,
                        running_mode=vision.RunningMode.VIDEO
                    )
                    self.landmarker = vision.HandLandmarker.create_from_options(options)
                    logger.info(f"MediaPipe HandLandmarker initialized from {model_path}")
                except Exception as e:
                    logger.error(f"Failed to initialize HandLandmarker: {e}")
                    self.enabled = False
            else:
                logger.error(f"Hand landmarker model not found at {model_path}")
                self.enabled = False
        
        # Gesture state
        self.cooldown = self.config.get('vision.gesture_cooldown', 0.8)
        self.last_gesture_time = 0
        self.last_gesture = Gesture.NONE
        
        # For tracking/drawing
        self.last_landmarks = None 
        self.hand_positions = []
        self.max_positions = 15

    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[Gesture], np.ndarray]:
        """
        Process frame and detect gestures.
        """
        if not self.enabled or self.landmarker is None or frame is None:
            return None, frame
            
        # Convert frame to MediaPipe Image
        # Note: BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int(time.time() * 1000)
        
        # Detect hands
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        
        gesture = Gesture.NONE
        self.last_landmarks = None # Reset
        
        if result.hand_landmarks:
            # We only use the first hand
            landmarks = result.hand_landmarks[0]
            
            # Prepare landmark list for compatibility with existing modules ([[x,y,z],...])
            h, w = frame.shape[:2]
            lmList = []
            for lm in landmarks:
                lmList.append([int(lm.x * w), int(lm.y * h), int(lm.z * w)]) # z scaled roughly
            
            # Draw landmarks manually
            self._draw_landmarks(frame, landmarks)
            
            # Wrap as compatible dict for AirDrawing and ASL
            self.last_landmarks = {
                "lmList": lmList,
                "landmarks_raw": landmarks
            }
            
            # Record wrist position for swipes (landmark 0)
            wrist = lmList[0] 
            self.hand_positions.append((wrist[0], wrist[1]))
            if len(self.hand_positions) > self.max_positions:
                self.hand_positions.pop(0)
                
            # Detect Swipe
            swipe = self._detect_swipe()
            if swipe:
                gesture = swipe
            else:
                # Recognize gesture based on raw landmarks
                gesture = self._recognize_gesture(landmarks)
            
        # Apply cooldown
        current_time = time.time()
        if gesture != Gesture.NONE:
            if current_time - self.last_gesture_time > self.cooldown:
                self.last_gesture_time = current_time
                self.last_gesture = gesture
                return gesture, frame
        
        return None, frame

    def _recognize_gesture(self, landmarks) -> Gesture:
        # Landmark indices: 0-Wrist, 4-ThumbTip, 8-IndexTip, 12-MiddleTip, 16-RingTip, 20-PinkyTip
        # Joints below tips: 2-3 (T), 6 (I), 10 (M), 14 (R), 18 (P)
        
        # Check fingers (except thumb)
        # Using Y coordinate: lower value means higher in image
        index_up = landmarks[8].y < landmarks[6].y
        middle_up = landmarks[12].y < landmarks[10].y
        ring_up = landmarks[16].y < landmarks[14].y
        pinky_up = landmarks[20].y < landmarks[18].y
        
        # [Index, Middle, Ring, Pinky]
        if index_up and middle_up and ring_up and pinky_up:
            return Gesture.OPEN_PALM
        elif not index_up and not middle_up and not ring_up and not pinky_up:
            return Gesture.FIST
        elif index_up and not middle_up and not ring_up and not pinky_up:
            return Gesture.POINT_UP
        elif index_up and middle_up and not ring_up and not pinky_up:
            return Gesture.PEACE_SIGN
        elif not index_up and not middle_up and not ring_up and not pinky_up:
            # Check for Point Down (Index lower than wrist?)
            if landmarks[8].y > landmarks[0].y:
                return Gesture.POINT_DOWN # Rough check
            
        return Gesture.NONE

    def _detect_swipe(self) -> Optional[Gesture]:
        if len(self.hand_positions) < self.max_positions:
            return None
            
        start_x = self.hand_positions[0][0]
        end_x = self.hand_positions[-1][0]
        delta_x = end_x - start_x
        
        threshold = 150 
        
        if delta_x > threshold:
            self.hand_positions.clear()
            return Gesture.SWIPE_RIGHT
        elif delta_x < -threshold:
            self.hand_positions.clear()
            return Gesture.SWIPE_LEFT
            
        return None

    def _draw_landmarks(self, frame, landmarks):
        """Draw hand landmarks manually on the frame."""
        h, w = frame.shape[:2]
        color = (0, 217, 255) # Cyan
        
        # Connections
        connections = [
            (0,1), (1,2), (2,3), (3,4), # Thumb
            (0,5), (5,6), (6,7), (7,8), # Index
            (0,9), (9,10), (10,11), (11,12), # Middle
            (0,13), (13,14), (14,15), (15,16), # Ring
            (0,17), (17,18), (18,19), (19,20), # Pinky
            (5,9), (9,13), (13,17), (0,5), (0,17) # Palm/Wrist
        ]
        
        for start_idx, end_idx in connections:
            start = landmarks[start_idx]
            end = landmarks[end_idx]
            cv2.line(frame, (int(start.x*w), int(start.y*h)), 
                     (int(end.x*w), int(end.y*h)), (200, 200, 200), 1)
            
        for lm in landmarks:
            cv2.circle(frame, (int(lm.x*w), int(lm.y*h)), 2, color, -1)

    def get_gesture_name(self, gesture: Gesture) -> str:
        names = {
            Gesture.OPEN_PALM: "Open Palm",
            Gesture.FIST: "Fist",
            Gesture.POINT_UP: "Point Up",
            Gesture.POINT_DOWN: "Point Down",
            Gesture.SWIPE_LEFT: "Swipe Left",
            Gesture.SWIPE_RIGHT: "Swipe Right",
            Gesture.PEACE_SIGN: "Peace Sign"
        }
        return names.get(gesture, "None")

    def cleanup(self):
        if self.landmarker:
            self.landmarker.close()
