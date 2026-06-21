"""
Air Drawing Engine for NOVA.
Tracks index fingertip and draws on a virtual canvas.
"""

import cv2
import numpy as np
import time
from collections import deque
from typing import Optional, Tuple, List, Dict
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)

class AirDrawingEngine:
    """Manages the virtual drawing canvas and finger tracking."""
    
    def __init__(self, width=1280, height=720):
        self.config = Config()
        self.width = width
        self.height = height
        
        # Canvas: BGR with 3 channels
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Drawing State
        self.active = False
        self.is_drawing = False
        self.last_point: Optional[Tuple[int, int]] = None
        
        # Tools
        self.brush_size = self.config.get('vision.drawing_brush_size', 5)
        self.current_color = (0, 217, 255)  # Cyan (BGR)
        self.colors = [
            (0, 217, 255),  # Cyan
            (0, 0, 255),    # Red
            (0, 255, 0),    # Green
            (0, 255, 255),  # Yellow
            (255, 255, 255) # White
        ]
        self.color_index = 0
        
        # Smoothing
        self.pts = deque(maxlen=self.config.get('vision.drawing_smoothing', 5))
        
        logger.info("Air Drawing Engine initialized")

    def reset_canvas(self):
        """Clear the virtual canvas."""
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.last_point = None
        self.pts.clear()
        logger.info("Drawing canvas cleared")

    def process_hand_data(self, hand_dict: Dict, frame_shape: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Extract fingertip position and update drawing state.
        hand_dict: The hand dictionary from cvzone HandDetector (contains lmList).
        """
        if not self.active or not hand_dict:
            self.last_point = None
            return None
            
        lmList = hand_dict.get("lmList", [])
        if not lmList:
            return None
            
        # Get index tip coordinates (Landmark 8)
        idx_tip = lmList[8] # [x, y, z]
        cx, cy = idx_tip[0], idx_tip[1]
        
        # Scaling logic if the virtual canvas size differes from camera feed size
        fh, fw = frame_shape
        canvas_x = int(cx * (self.width / fw))
        canvas_y = int(cy * (self.height / fh))
        
        return (canvas_x, canvas_y)

    def draw(self, point: Tuple[int, int], is_fist: bool = False):
        """Apply drawing to the canvas."""
        if not self.active:
            return
            
        # Draw only if not a fist (pen down)
        if not is_fist:
            self.is_drawing = True
            if self.last_point is not None:
                cv2.line(self.canvas, self.last_point, point, self.current_color, self.brush_size)
            self.last_point = point
        else:
            self.is_drawing = False
            self.last_point = None

    def get_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Merge the drawing canvas with the camera frame."""
        if not self.active:
            return frame
            
        # Resize canvas to match frame if necessary
        fh, fw = frame.shape[:2]
        if (fh, fw) != (self.height, self.width):
            drawing = cv2.resize(self.canvas, (fw, fh))
        else:
            drawing = self.canvas
            
        # Create a mask of the drawing
        img_gray = cv2.cvtColor(drawing, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(img_gray, 10, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        
        # Black out the area of the drawing in the frame
        img1_bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
        
        # Take only region of drawing from drawing image
        img2_fg = cv2.bitwise_and(drawing, drawing, mask=mask)
        
        # Put drawing in frame and return
        res = cv2.add(img1_bg, img2_fg)
        return res

    def next_color(self):
        """Switch to the next available color."""
        self.color_index = (self.color_index + 1) % len(self.colors)
        self.current_color = self.colors[self.color_index]
        logger.info(f"Color switched to: {self.current_color}")
