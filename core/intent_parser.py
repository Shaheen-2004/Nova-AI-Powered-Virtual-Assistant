"""Intent parser for NOVA - Routes commands to appropriate handlers."""

import re
from typing import Tuple, Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class Intent:
    """Represents a parsed user intent."""
    
    # Intent types
    CONVERSATION = "conversation"
    SYSTEM_COMMAND = "system_command"
    APP_LAUNCH = "app_launch"
    WEB_SEARCH = "web_search"
    VISION_QUERY = "vision_query"
    TIME_QUERY = "time_query"
    WEATHER_QUERY = "weather_query"
    MEDIA_CONTROL = "media_control"
    POWER_MODE = "power_mode"
    TYPING_COMMAND = "typing_command"
    DRAWING_CONTROL = "drawing_control"
    
    def __init__(self, intent_type: str, data: Optional[Dict[str, Any]] = None):
        self.type = intent_type
        self.data = data or {}
    
    def __repr__(self):
        return f"Intent(type={self.type}, data={self.data})"


class IntentParser:
    """Parses user input and determines intent."""
    
    # Command patterns
    PATTERNS = {
        # App launching
        Intent.APP_LAUNCH: [
            r"(?:open|launch|start|run|take\s+me\s+to|go\s+to)\s+(.+)",
        ],
        
        # Web search
        Intent.WEB_SEARCH: [
            r"(?:search|google|look up|find)\s+(?:for\s+)?(.+)",
        ],
        
        # Vision queries
        Intent.VISION_QUERY: [
            r"what\s+(?:do\s+)?you\s+see",
            r"describe\s+(?:what\s+)?(?:you\s+)?(?:see|can see)",
            r"what(?:'s|\s+is)\s+(?:in\s+)?(?:front\s+of\s+)?(?:you|the\s+camera)",
            r"(?:identify|recognize|scan)(?:\s+(?:the|this|that|these))?(\s+objects?)?",
            r"what(?:\s+is|'s)\s+this",
        ],
        
        # Time queries
        Intent.TIME_QUERY: [
            r"what\s+time\s+is\s+it",
            r"what(?:'s|\s+is)\s+the\s+time",
            r"tell\s+me\s+the\s+time",
        ],
        
        # Weather queries
        Intent.WEATHER_QUERY: [
            r"what(?:'s|\s+is)\s+the\s+weather",
            r"how(?:'s|\s+is)\s+the\s+weather",
            r"weather\s+(?:forecast|report)",
        ],
        
        # Media control
        Intent.MEDIA_CONTROL: [
            r"(play|pause|stop|next|previous|volume\s+up|volume\s+down|mute)",
        ],
        
        # Power mode control
        Intent.POWER_MODE: [
            r"(?:set|switch|change)\s+(?:to\s+)?(?:power\s+)?(?:mode\s+)?(?:to\s+)?(performance|balanced|custom|smart|power\s+saver)",
            r"(?:enable|activate)\s+(performance|balanced|custom|smart|power\s+saver)\s+mode",
            r"what(?:'s|\s+is)\s+(?:the\s+)?(?:current\s+)?power\s+mode",
            r"(?:check|show|tell)\s+(?:me\s+)?(?:the\s+)?power\s+mode",
        ],
        
        # System commands
        Intent.SYSTEM_COMMAND: [
            r"(screenshot|lock\s+screen|shutdown|restart|sleep)",
        ],
        
        # Typing commands
        Intent.TYPING_COMMAND: [
            r"(?:type\s+this|write\s+this|automatic\s+typing|type)\s+[\"']?(.*?)[\"']?$",
            r"(?:type|write)\s+(.+)",
        ],
        
        # Drawing commands
        Intent.DRAWING_CONTROL: [
            r"(?:start|activate|open)\s+(?:air\s+)?drawing",
            r"(?:stop|exit|close|clear)\s+(?:air\s+)?drawing",
        ],
    }
    
    def __init__(self):
        """Initialize intent parser."""
        logger.info("Intent parser initialized")
    
    def parse(self, text: str) -> Intent:
        """
        Parse user input and determine intent.
        
        Args:
            text: User's input text
        
        Returns:
            Intent object with type and extracted data
        """
        if not text:
            return Intent(Intent.CONVERSATION)
        
        text_lower = text.lower().strip()
        
        # Check each pattern type
        for intent_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    # Extract data from capture groups
                    data = {}
                    if match.groups():
                        if intent_type == Intent.APP_LAUNCH:
                            data['app_name'] = match.group(1).strip()
                        elif intent_type == Intent.WEB_SEARCH:
                            data['query'] = match.group(1).strip()
                        elif intent_type == Intent.MEDIA_CONTROL:
                            data['action'] = match.group(1).strip()
                        elif intent_type == Intent.TYPING_COMMAND:
                            data['text'] = match.group(1).strip()
                        elif intent_type == Intent.SYSTEM_COMMAND:
                            data['command'] = match.group(1).strip()
                        elif intent_type == Intent.POWER_MODE:
                            # Check if it's a query or a set command
                            if 'what' in text_lower or 'check' in text_lower or 'show' in text_lower or 'tell' in text_lower:
                                data['action'] = 'get'
                            else:
                                data['action'] = 'set'
                                data['mode'] = match.group(1).strip() if match.groups() else None
                    
                    logger.info(f"Parsed intent: {intent_type} - {data}")
                    return Intent(intent_type, data)
        
        # Default to conversation
        logger.info(f"No specific intent matched, defaulting to conversation")
        return Intent(Intent.CONVERSATION, {'text': text})
    
    def is_command(self, text: str) -> bool:
        """
        Check if text is a command (not conversation).
        
        Args:
            text: User's input text
        
        Returns:
            True if text is a command
        """
        intent = self.parse(text)
        return intent.type != Intent.CONVERSATION
