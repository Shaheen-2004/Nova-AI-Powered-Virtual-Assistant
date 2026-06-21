Based on your uploaded project files, this is a professional GitHub README description for your **NOVA AI Assistant** project. It highlights the voice assistant, AI integration, computer vision, gesture control, system automation, and app launching capabilities found in your code.   

# 🤖 NOVA - Intelligent Vision AI Assistant

A professional-grade AI-powered desktop assistant inspired by JARVIS from Iron Man. NOVA combines voice interaction, computer vision, gesture recognition, AI conversation, application control, and system automation into a single intelligent assistant.

![NOVA Banner](https://raw.githubusercontent.com/ultralytics/assets/main/yolov8/banner-yolov8.png)

## 🌟 Key Features

* 🎙️ **Voice Assistant**

  * Real-time Speech-to-Text using Google Speech Recognition.
  * Natural Text-to-Speech responses using Windows SAPI.
  * Smart listening indicators and voice feedback.

* 🧠 **AI Brain Integration**

  * Powered by Claude AI for intelligent conversations.
  * Context-aware responses with memory support.
  * JARVIS-inspired personality and interaction style.

* 👁️ **Computer Vision**

  * Real-time camera monitoring.
  * Object detection and scene understanding.
  * Visual query support such as:

    * "What do you see?"
    * "Identify this object"
    * "Describe the scene"

* ✋ **Gesture Recognition**

  * Hand gesture-based control.
  * Open Palm activation system.
  * Air Drawing support for interactive control.

* 💻 **System Automation**

  * Screenshot capture.
  * Screen lock.
  * Shutdown, restart, and sleep controls.
  * Volume management and media control.

* 🚀 **Smart Application Launcher**

  * Open applications using natural voice commands.
  * Launch browsers, editors, media apps, and Windows utilities.
  * Dynamic indexing of installed Windows applications.

* 🌐 **Web & Productivity Integration**

  * Web search commands.
  * Quick access to YouTube, LinkedIn, Chrome, VS Code, Spotify, Discord, and more.

## 🏗️ Project Architecture

```text
NOVA/
│
├── main.py                    # Main application
│
├── core/
│   ├── ai_brain.py            # Claude AI integration
│   ├── speech_handler.py      # STT & TTS engine
│   └── intent_parser.py       # Command routing
│
├── system/
│   ├── app_launcher.py        # Application launcher
│   └── system_commands.py     # OS automation
│
├── vision/
│   ├── object_detector.py     # Object detection
│   ├── gesture_recognition.py # Hand tracking
│   └── camera_thread.py       # Camera management
│
├── config.yaml
├── .env
└── requirements.txt
```

## 🎯 Supported Commands

### Voice Commands

```text
Open Chrome
Launch VS Code
Search Python tutorials
Take Screenshot
Lock Screen
Shutdown Computer
What time is it?
What's the weather?
Start Air Drawing
What do you see?
```

## 🚀 Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file:

```env
ANTHROPIC_API_KEY=your_api_key
OPENAI_API_KEY=optional
ELEVENLABS_API_KEY=optional
PICOVOICE_API_KEY=optional
```

### Run NOVA

```bash
python main.py
```

## 🛠️ Technologies Used

* Python 3.11+
* Claude API
* OpenCV
* MediaPipe
* SpeechRecognition
* PyAutoGUI
* PyTTSX3
* Windows SAPI
* PyQt
* NumPy

## 🎯 Future Enhancements

* Face Recognition
* Smart Home Integration
* LLM Agent Workflows
* Wake Word Detection
* Multi-Agent AI System
* Custom Computer Vision Models
* IoT Device Control

## 🛡️ License

This project is intended for educational, research, and prototyping purposes.

---

