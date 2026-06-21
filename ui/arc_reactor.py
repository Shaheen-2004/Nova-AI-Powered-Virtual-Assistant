"""
Arc Reactor UI Component for NOVA.
A custom PyQt6 widget with animated states and reactive behaviors.
"""

import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QPen, QBrush, QConicalGradient

class ArcReactor(QWidget):
    """Animated Arc Reactor component inspired by Iron Man's chest circle."""
    
    # States
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    VISION = "vision"
    GESTURE = "gesture"
    ERROR = "error"
    POWER = "power"
    
    def __init__(self, parent=None, size=250):
        super().__init__(parent)
        self.setFixedSize(size, size)
        
        # State
        self.state = self.IDLE
        self.brightness = 0.5
        self.rotation_angle = 0
        self.pulse_value = 0.0
        self.pulse_direction = 1
        
        # Animation parameters
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
        
        # Colors
        self.colors = {
            self.IDLE: QColor(0, 217, 255, 200),
            self.LISTENING: QColor(0, 217, 255, 255),
            self.PROCESSING: QColor(0, 255, 204, 255),
            self.SPEAKING: QColor(0, 170, 255, 255),
            self.VISION: QColor(0, 217, 255, 255),
            self.GESTURE: QColor(255, 255, 255, 255),
            self.ERROR: QColor(255, 51, 102, 255),
            self.POWER: QColor(0, 217, 255, 255)
        }
        
    def set_state(self, state):
        """Update the reactor state."""
        if state in self.colors:
            self.state = state
            
    def update_animation(self):
        """Update animation variables based on current state."""
        # Rotation logic
        if self.state == self.PROCESSING:
            self.rotation_angle += 8
        elif self.state == self.LISTENING:
            self.rotation_angle += 4
        elif self.state == self.VISION:
            self.rotation_angle += 3
        else:
            self.rotation_angle += 1
            
        if self.rotation_angle >= 360:
            self.rotation_angle = 0
            
        # Pulse logic
        pulse_speed = 0.01
        if self.state == self.PROCESSING:
            pulse_speed = 0.05
        elif self.state == self.LISTENING:
            pulse_speed = 0.03
        elif self.state == self.SPEAKING:
            pulse_speed = 0.04
        elif self.state == self.ERROR:
            pulse_speed = 0.05
            
        self.pulse_value += pulse_speed * self.pulse_direction
        if self.pulse_value >= 1.0:
            self.pulse_value = 1.0
            self.pulse_direction = -1
        elif self.pulse_value <= 0.0:
            self.pulse_value = 0.0
            self.pulse_direction = 1
            
        if self.state == self.IDLE:
            self.brightness = 0.3 + (self.pulse_value * 0.3)
        else:
            self.brightness = 0.5 + (self.pulse_value * 0.5)
            
        self.update()
        
    def paintEvent(self, event):
        """Draw the Arc Reactor."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = self.width() / 2 - 10
        
        # 1. Background Glow
        self.draw_glow(painter, center, radius)
        
        # 2. Outer Ring (Segments)
        self.draw_outer_ring(painter, center, radius)
        
        # 3. Middle Ring (Rotating lines)
        self.draw_middle_ring(painter, center, radius * 0.7)
        
        # 4. Inner Core
        self.draw_core(painter, center, radius * 0.4)
        
    def draw_glow(self, painter, center, radius):
        """Draw soft radial glow behind the reactor."""
        color = self.colors[self.state]
        glow_radius = radius * (1.2 + self.pulse_value * 0.1)
        
        gradient = QRadialGradient(center, glow_radius)
        gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), int(100 * self.brightness)))
        gradient.setColorAt(1, Qt.GlobalColor.transparent)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, glow_radius, glow_radius)
        
    def draw_outer_ring(self, painter, center, radius):
        """Draw the segmented outer ring."""
        color = self.colors[self.state]
        painter.setPen(QPen(color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        
        num_segments = 12
        span_angle = 360 / num_segments
        padding = 5
        
        for i in range(num_segments):
            start_angle = (i * span_angle + self.rotation_angle * 0.5) * 16
            sweep_angle = (span_angle - padding) * 16
            
            # Highlight some segments in processing mode
            if self.state == self.PROCESSING and (i + self.pulse_value * num_segments) % num_segments < 3:
                painter.setPen(QPen(Qt.GlobalColor.white, 5))
            else:
                painter.setPen(QPen(color, 4))
                
            painter.drawArc(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), 
                           int(start_angle), int(sweep_angle))
            
    def draw_middle_ring(self, painter, center, radius):
        """Draw the rotating energy lines."""
        color = self.colors[self.state]
        
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle)
        
        pen = QPen(color, 2)
        painter.setPen(pen)
        
        num_lines = 8
        for i in range(num_lines):
            angle = (i * 360 / num_lines)
            x1 = radius * 0.8 * math.cos(math.radians(angle))
            y1 = radius * 0.8 * math.sin(math.radians(angle))
            x2 = radius * 1.1 * math.cos(math.radians(angle))
            y2 = radius * 1.1 * math.sin(math.radians(angle))
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            
        # Draw a thin circle connecting them
        painter.drawEllipse(QRectF(-radius, -radius, radius * 2, radius * 2))
        painter.restore()
        
    def draw_core(self, painter, center, radius):
        """Draw the central pulsing core."""
        color = self.colors[self.state]
        
        # Outer core circle
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)
        
        # Inner glow
        inner_radius = radius * (0.6 + self.pulse_value * 0.2)
        gradient = QRadialGradient(center, inner_radius)
        gradient.setColorAt(0, Qt.GlobalColor.white)
        gradient.setColorAt(0.5, color)
        gradient.setColorAt(1, Qt.GlobalColor.transparent)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, inner_radius, inner_radius)
        
        # Scanning lines for VISION state
        if self.state == self.VISION:
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            y = center.y() - radius + (self.pulse_value * 2 * radius)
            painter.drawLine(QPointF(center.x() - radius, y), QPointF(center.x() + radius, y))
