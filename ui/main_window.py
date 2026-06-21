"""Main window for NOVA - PyQt6 interface."""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime
from utils.logger import get_logger
from utils.config import Config
from ui.arc_reactor import ArcReactor

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with futuristic JARVIS-inspired design."""
    
    # Signals
    transcript_updated = pyqtSignal(str, str)  # role, message
    status_updated = pyqtSignal(str, bool)  # component, active
    listen_requested = pyqtSignal()  # manual listen trigger
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        self.config = Config()
        self.setup_ui()
        self.apply_theme()
        
        # Update time periodically
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # Update every second
        
        logger.info("Main window initialized")
    
    def setup_ui(self):
        """Set up the user interface."""
        # Window properties
        width = self.config.get('ui.window_width', 1400)
        height = self.config.get('ui.window_height', 900)
        
        self.setWindowTitle("NOVA - Intelligent Vision Assistant")
        self.setGeometry(100, 100, width, height)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        central_widget.setLayout(main_layout)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Visualizer placeholder
        visualizer = self.create_visualizer()
        main_layout.addWidget(visualizer, stretch=1)
        
        # Bottom panel (Camera + Transcript)
        bottom_panel = self.create_bottom_panel()
        main_layout.addWidget(bottom_panel, stretch=2)
        
        # Status bar
        status_bar = self.create_status_bar()
        main_layout.addWidget(status_bar)
    
    def create_header(self) -> QWidget:
        """Create header with logo, time, and weather."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(80)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        header.setLayout(layout)
        
        # NOVA logo
        logo = QLabel("◉ NOVA")
        logo.setObjectName("logo")
        logo_font = QFont(self.config.get('ui.font_family', 'Segoe UI'), 28, QFont.Weight.Bold)
        logo.setFont(logo_font)
        layout.addWidget(logo)
        
        layout.addStretch()
        
        # Time display
        self.time_label = QLabel()
        self.time_label.setObjectName("timeLabel")
        time_font = QFont(self.config.get('ui.font_family', 'Segoe UI'), 16)
        self.time_label.setFont(time_font)
        self.update_time()
        layout.addWidget(self.time_label)
        
        return header
    
    def create_visualizer(self) -> QWidget:
        """Create animated Arc Reactor centerpiece."""
        visualizer = QFrame()
        visualizer.setObjectName("visualizer")
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        visualizer.setLayout(layout)
        
        # Arc Reactor
        self.arc_reactor = ArcReactor(size=250)
        layout.addWidget(self.arc_reactor)
        
        return visualizer
    
    def create_bottom_panel(self) -> QWidget:
        """Create bottom panel with camera feed and transcript."""
        panel = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(15)
        panel.setLayout(layout)
        
        # Camera feed panel
        camera_panel = QFrame()
        camera_panel.setObjectName("cameraPanel")
        camera_layout = QVBoxLayout()
        camera_panel.setLayout(camera_layout)
        
        camera_label = QLabel("📷 Camera Feed")
        camera_label.setObjectName("panelTitle")
        camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_layout.addWidget(camera_label)
        
        self.camera_display = QLabel("Camera will appear here")
        self.camera_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_display.setMinimumSize(400, 300)
        self.camera_display.setObjectName("cameraDisplay")
        camera_layout.addWidget(self.camera_display)
        
        # ASL Overlay Info
        asl_info_layout = QHBoxLayout()
        self.current_letter_label = QLabel("Letter: -")
        self.current_letter_label.setObjectName("aslLabel")
        self.current_word_label = QLabel("Spelling: ")
        self.current_word_label.setObjectName("aslLabel")
        asl_info_layout.addWidget(self.current_letter_label)
        asl_info_layout.addWidget(self.current_word_label)
        camera_layout.addLayout(asl_info_layout)
        
        layout.addWidget(camera_panel, stretch=2)
        
        # Transcript panel
        transcript_panel = QFrame()
        transcript_panel.setObjectName("transcriptPanel")
        transcript_layout = QVBoxLayout()
        transcript_panel.setLayout(transcript_layout)
        
        transcript_label = QLabel("💬 Conversation")
        transcript_label.setObjectName("panelTitle")
        transcript_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        transcript_layout.addWidget(transcript_label)
        
        self.transcript_display = QTextEdit()
        self.transcript_display.setReadOnly(True)
        self.transcript_display.setObjectName("transcriptDisplay")
        transcript_layout.addWidget(self.transcript_display)
        
        layout.addWidget(transcript_panel, stretch=1)
        
        # Connect signal
        self.transcript_updated.connect(self.add_transcript_message)
        
        return panel
    
    def create_status_bar(self) -> QWidget:
        """Create status indicators and control buttons."""
        status_bar = QFrame()
        status_bar.setObjectName("statusBar")
        status_bar.setFixedHeight(60)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 5, 15, 5)
        status_bar.setLayout(layout)
        
        # Manual Listen Button
        self.listen_button = QPushButton("🎤 LISTEN")
        self.listen_button.setObjectName("listenButton")
        self.listen_button.setFixedWidth(120)
        self.listen_button.clicked.connect(self.listen_requested.emit)
        layout.addWidget(self.listen_button)
        
        layout.addSpacing(20)
        
        # Status indicators
        self.status_indicators = {}
        indicators = [
            ('mic', '🎤 Mic'),
            ('vision', '👁️ Vision'),
            ('gestures', '🤚 Gestures'),
            ('ai', '🧠 AI'),
            ('audio', '🔊 Audio')
        ]
        
        for key, label_text in indicators:
            label = QLabel(label_text)
            label.setObjectName(f"status_{key}")
            layout.addWidget(label)
            self.status_indicators[key] = label
        
        layout.addStretch()
        
        return status_bar
    
    def apply_theme(self):
        """Apply futuristic dark theme with glassmorphism."""
        bg_color = self.config.get('ui.background_color', '#0a0e27')
        accent_color = self.config.get('ui.accent_color', '#00d9ff')
        transparency = self.config.get('ui.transparency', 0.85)
        
        # Calculate semi-transparent background
        bg_alpha = int(transparency * 255)
        
        stylesheet = f"""
        QMainWindow {{
            background-color: {bg_color};
        }}
        
        QFrame#header {{
            background-color: rgba(10, 14, 39, 200);
            border: 2px solid {accent_color};
            border-radius: 15px;
        }}
        
        QLabel#logo {{
            color: {accent_color};
            font-weight: bold;
        }}
        
        QLabel#timeLabel {{
            color: white;
        }}
        
        QFrame#visualizer {{
            background-color: rgba(10, 14, 39, 150);
            border: 2px solid {accent_color};
            border-radius: 20px;
        }}
        
        QLabel#visualizerLabel {{
            color: {accent_color};
        }}
        
        QFrame#cameraPanel, QFrame#transcriptPanel {{
            background-color: rgba(10, 14, 39, 200);
            border: 2px solid {accent_color};
            border-radius: 15px;
            padding: 10px;
        }}
        
        QLabel#panelTitle {{
            color: {accent_color};
            font-size: 16px;
            font-weight: bold;
            padding: 5px;
        }}
        
        QLabel#cameraDisplay {{
            background-color: rgba(0, 0, 0, 100);
            border: 1px solid {accent_color};
            border-radius: 10px;
            color: #666;
        }}
        
        QTextEdit#transcriptDisplay {{
            background-color: rgba(0, 0, 0, 150);
            border: 1px solid {accent_color};
            border-radius: 10px;
            color: white;
            font-size: 14px;
            padding: 10px;
        }}
        
        QFrame#statusBar {{
            background-color: rgba(10, 14, 39, 200);
            border: 2px solid {accent_color};
            border-radius: 10px;
        }}
        
        QLabel[objectName^="status_"] {{
            color: #666;
            font-size: 12px;
            padding: 5px 10px;
        }}
        QLabel#aslLabel {{
            color: #00d9ff;
            font-size: 18px;
            font-weight: bold;
            background-color: rgba(0, 0, 0, 100);
            padding: 5px 15px;
            border-radius: 5px;
        }}
        """
        
        self.setStyleSheet(stylesheet)
    
    def update_time(self):
        """Update time display."""
        now = datetime.now()
        time_str = now.strftime("%I:%M:%S %p")
        date_str = now.strftime("%A, %B %d")
        self.time_label.setText(f"{time_str}\n{date_str}")
    
    def add_transcript_message(self, role: str, message: str):
        """
        Add message to transcript.
        
        Args:
            role: 'user', 'nova', or 'system'
            message: Message text
        """
        if role.lower() == "system":
            color = "#888888"
            prefix = "[SYSTEM]:"
        else:
            color = "#00d9ff" if role.lower() == "nova" else "#ffffff"
            prefix = "NOVA:" if role.lower() == "nova" else "You:"
        
        self.transcript_display.append(
            f'<span style="color: {color}; font-weight: bold;">{prefix}</span> '
            f'<span style="color: {"#aaaaaa" if role.lower() == "system" else "white"};">{message}</span><br>'
        )
    
    def update_status(self, component: str, active: bool):
        """
        Update status indicator.
        
        Args:
            component: Component name (mic, vision, gestures, ai, audio)
            active: Whether component is active
        """
        if component in self.status_indicators:
            label = self.status_indicators[component]
            color = "#00ff00" if active else "#666"
            label.setStyleSheet(f"color: {color};")
