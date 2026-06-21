"""Object detection using YOLOv8."""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from ultralytics import YOLO
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class Detection:
    """Represents a single object detection."""
    
    def __init__(self, class_name: str, confidence: float, bbox: Tuple[int, int, int, int]):
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox  # (x1, y1, x2, y2)
    
    def __repr__(self):
        return f"Detection({self.class_name}, {self.confidence:.2f})"


class ObjectDetector:
    """YOLOv8-based object detector."""
    
    def __init__(self):
        """Initialize YOLO model."""
        self.config = Config()
        
        # Model configuration
        model_name = self.config.get('vision.yolo_model', 'yolov8n.pt')
        self.confidence_threshold = self.config.get('vision.confidence_threshold', 0.5)
        self.max_detections = self.config.get('vision.max_detections', 10)
        
        # Load model
        logger.info(f"Loading YOLO model: {model_name}")
        try:
            self.model = YOLO(model_name)
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            logger.info("Model will be downloaded on first use")
            self.model = YOLO(model_name)
        
        self.enabled = self.config.get('vision.object_detection', True)
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect objects in a frame.
        
        Args:
            frame: Input image (BGR format from OpenCV)
        
        Returns:
            List of Detection objects
        """
        if not self.enabled or frame is None:
            return []
        
        try:
            # Run inference with optimized image size for speed
            # imgsz=320 is very fast, 640 is standard. We'll use 480 as a balance.
            results = self.model(frame, verbose=False, imgsz=480)[0]
            
            detections = []
            
            # Process results
            for box in results.boxes:
                confidence = float(box.conf[0])
                
                if confidence < self.confidence_threshold:
                    continue
                
                # Get class name
                class_id = int(box.cls[0])
                class_name = results.names[class_id]
                
                # Get bounding box
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                
                detections.append(Detection(class_name, confidence, (x1, y1, x2, y2)))
                
                if len(detections) >= self.max_detections:
                    break
            
            return detections
            
        except Exception as e:
            logger.error(f"Object detection error: {e}")
            return []
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Draw bounding boxes and labels on frame.
        
        Args:
            frame: Input image
            detections: List of detections to draw
        
        Returns:
            Frame with drawn detections
        """
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 217, 255), 2)  # Cyan color
            
            # Draw label background
            label = f"{det.class_name} {det.confidence:.2f}"
            (label_width, label_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )
            
            cv2.rectangle(
                frame,
                (x1, y1 - label_height - 10),
                (x1 + label_width, y1),
                (0, 217, 255),
                -1
            )
            
            # Draw label text
            cv2.putText(
                frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (10, 14, 39),  # Dark background color
                2
            )
        
        return frame
    
    def get_description(self, detections: List[Detection]) -> str:
        """
        Get natural language description of detections.
        
        Args:
            detections: List of detections
        
        Returns:
            Human-readable description
        """
        if not detections:
            return "I don't see any recognizable objects at the moment."
        
        # Count objects by class
        object_counts = {}
        for det in detections:
            object_counts[det.class_name] = object_counts.get(det.class_name, 0) + 1
        
        # Build description
        items = []
        for obj, count in object_counts.items():
            if count == 1:
                items.append(f"a {obj}")
            else:
                items.append(f"{count} {obj}s")
        
        if len(items) == 1:
            return f"I see {items[0]}."
        elif len(items) == 2:
            return f"I can see {items[0]} and {items[1]}."
        else:
            all_but_last = ", ".join(items[:-1])
            return f"I've identified {all_but_last}, and {items[-1]}."
