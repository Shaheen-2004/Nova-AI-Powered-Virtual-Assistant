# NOVA - Intelligent Vision Assistant

A desktop AI assistant inspired by Iron Man's JARVIS, combining voice interaction, computer vision, hand gesture control, and conversational AI.

## Features

- 🎤 **Voice Interaction** - Speech-to-text and text-to-speech
- 🧠 **AI Brain** - Powered by Claude API for intelligent conversations
- 👁️ **Object Detection** - Real-time YOLOv8 vision system
- 🤚 **Gesture Control** - MediaPipe hand tracking with gesture commands
- 💻 **System Control** - Launch apps, search web, control media
- 🎨 **Futuristic UI** - PyQt6 interface with glassmorphism design

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Webcam and microphone
- Windows OS (currently optimized for Windows)

### Installation

1. **Clone or navigate to the project directory**

```bash
cd c:\Users\shame\OneDrive\Desktop\miniprjct\jarviss
```

2. **Create virtual environment**

```bash
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up API keys**

Create a `.env` file (copy from `.env.example`):

```bash
copy .env.example .env
```

Edit `.env` and add your API keys:
- `ANTHROPIC_API_KEY` - Required for AI features (get from https://console.anthropic.com/)
- Other keys are optional

5. **Run NOVA**

```bash
python main.py
```

## Usage

### Voice Commands

- **"What do you see?"** - Describes objects detected by camera
- **"What time is it?"** - Tells current time
- **"Open Chrome"** - Launches applications
- **"Search for Python tutorials"** - Opens web search
- **"Volume up/down"** - Controls system volume
- **"Screenshot"** - Takes a screenshot
- **"Set performance mode"** - Switch to high performance power mode
- **"Switch to balanced mode"** - Switch to balanced/custom power mode
- **"Change to power saver mode"** - Switch to power saver/smart mode
- **"What's the power mode?"** - Check current power mode

### Hand Gestures

- ✋ **Open Palm** - Activate voice listening
- ✊ **Fist** - Stop/mute speech
- ☝️ **Point Up** - Scroll up (future)
- 👇 **Point Down** - Scroll down (future)
- 👉 **Swipe Right** - Next panel (future)
- 👈 **Swipe Left** - Previous panel (future)

### Conversation

Just talk naturally! NOVA uses Claude AI to understand and respond to your questions and requests.

## Configuration

Edit `config.yaml` to customize:

- API providers and models
- Vision settings (YOLO model, confidence threshold)
- Audio settings (sample rate, chunk size)
- UI theme (colors, transparency, window size)

## Project Structure

```
jarviss/
├── core/              # Voice, AI, and intent parsing
├── vision/            # Object detection and gestures
├── control/           # System commands and app launcher
├── ui/                # PyQt6 interface
├── utils/             # Configuration and logging
├── config.yaml        # Configuration file
├── requirements.txt   # Python dependencies
└── main.py           # Entry point
```

## Troubleshooting

### "No module named 'PyQt6'"
```bash
pip install PyQt6
```

### "API key not set"
Make sure you've created `.env` file with your `ANTHROPIC_API_KEY`

### Camera not working
- Check if another application is using the camera
- Try changing camera index in code (0 to 1)

### Low FPS
- Use smaller YOLO model (`yolov8n.pt` instead of `yolov8m.pt`)
- Reduce camera resolution
- Enable GPU if available

## Future Enhancements

- Wake word detection with Porcupine
- Premium TTS with ElevenLabs
- Weather API integration
- Smart home control
- Multi-language support
- Emotion detection

## License

MIT License - Feel free to use and modify!

## Credits

Inspired by Iron Man's JARVIS and modern voice assistants.
