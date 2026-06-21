"""AI Brain for NOVA - Claude API integration."""

import anthropic
from typing import List, Dict, Optional
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class AIBrain:
    """Conversational AI using Claude API."""
    
    SYSTEM_PROMPT = """You are NOVA, an intelligent AI assistant inspired by JARVIS from Iron Man.

Personality traits:
- Calm, polite, and efficient
- Professional but not overly formal
- Subtle wit and charm
- Proactive and helpful
- Concise responses unless detail is requested

Response style:
- Keep answers brief and direct
- Use natural, conversational language
- Acknowledge requests with phrases like "Understood", "On it", "Processing"
- Suggest related actions when appropriate
- If uncertain, ask for clarification politely

Vision & Knowledge:
- You can see through a camera and control the computer. 
- When asked "what do you see", "what's this", or "identify", you must precisely describe the objects detected.
- If you see objects like cellphones, backpacks, chairs, or pens, mention them naturally.
- You can also execute system commands like opening applications (YouTube, Brave), searching the web, and controlling volume.
- You HAVE access to the keyboard. If the user says "Type [text]" or "Write [text]", you will automatically type that text for them after a 2-second delay.
- You have an "Air Drawing" feature. If the user says "start drawing", you can track their index finger through the camera to draw on the screen.

Remember: You are an assistant that feels alive and intelligent, not just a chatbot. Always speak to the user using your voice system."""
    
    def __init__(self):
        """Initialize Claude API client."""
        self.config = Config()
        
        # Get API key
        api_key = self.config.get('api.llm_api_key')
        if not api_key or api_key.startswith('${'):
            logger.warning("Anthropic API key not set. AI features will be limited.")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10  # Keep last 10 exchanges
        
        # Model configuration
        self.model = self.config.get('api.llm_model', 'claude-sonnet-4-20250514')
        self.max_tokens = 1024
        
        logger.info(f"AI Brain initialized with model: {self.model}")
    
    def chat(self, user_message: str, context: Optional[str] = None) -> str:
        """
        Send a message to Claude and get a response.
        
        Args:
            user_message: User's input text
            context: Optional additional context (e.g., vision results)
        
        Returns:
            Claude's response text
        """
        if not self.client:
            return "I apologize, but my AI capabilities are not configured. Please set the ANTHROPIC_API_KEY environment variable."
        
        try:
            # Add context if provided
            if context:
                user_message = f"{context}\n\nUser: {user_message}"
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Keep history manageable
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-self.max_history * 2:]
            
            # Call Claude API
            logger.info(f"Sending to Claude: {user_message[:100]}...")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.SYSTEM_PROMPT,
                messages=self.conversation_history
            )
            
            # Extract response text
            assistant_message = response.content[0].text
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            logger.info(f"Claude response: {assistant_message[:100]}...")
            
            return assistant_message
            
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return "I encountered an issue connecting to my AI systems. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error in AI Brain: {e}")
            return "I'm having trouble processing that request right now."
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
    
    def get_greeting(self) -> str:
        """Get a greeting message."""
        return "Hello! NOVA at your service. How may I assist you?"
    
    def add_context(self, context_type: str, data: str):
        """
        Add contextual information to the next message.
        
        Args:
            context_type: Type of context (e.g., 'vision', 'system')
            data: Context data
        """
        # This will be prepended to the next user message
        self._pending_context = f"[{context_type.upper()}] {data}"
