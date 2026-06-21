"""System commands for NOVA - OS-level control."""

import subprocess
import webbrowser
import pyautogui
from datetime import datetime
from typing import Optional
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class SystemCommands:
    """Handles system-level commands."""
    
    def __init__(self):
        """Initialize system commands handler."""
        self.config = Config()
        self.enabled = self.config.get('system.enable_system_control', True)
        logger.info("System commands initialized")
    
    def execute_command(self, command: str) -> str:
        """
        Execute a system command.
        
        Args:
            command: Command to execute
        
        Returns:
            Response message
        """
        if not self.enabled:
            return "System control is disabled."
        
        command = command.lower().strip()
        
        try:
            if command == "screenshot":
                return self.take_screenshot()
            elif command == "lock screen":
                return self.lock_screen()
            elif command == "shutdown":
                return self.shutdown()
            elif command == "restart":
                return self.restart()
            elif command == "sleep":
                return self.sleep()
            else:
                return f"Unknown system command: {command}"
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return f"Failed to execute command: {str(e)}"
    
    def take_screenshot(self) -> str:
        """Take a screenshot."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            
            logger.info(f"Screenshot saved: {filename}")
            return f"Screenshot saved as {filename}"
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return "Failed to take screenshot"
    
    def lock_screen(self) -> str:
        """Lock the screen."""
        try:
            # Windows
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'])
            logger.info("Screen locked")
            return "Locking screen"
        except Exception as e:
            logger.error(f"Lock screen error: {e}")
            return "Failed to lock screen"
    
    def shutdown(self) -> str:
        """Shutdown the computer."""
        try:
            # Windows
            subprocess.run(['shutdown', '/s', '/t', '10'])
            logger.info("Shutdown initiated")
            return "Shutting down in 10 seconds. Use 'shutdown /a' to cancel."
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            return "Failed to shutdown"
    
    def restart(self) -> str:
        """Restart the computer."""
        try:
            # Windows
            subprocess.run(['shutdown', '/r', '/t', '10'])
            logger.info("Restart initiated")
            return "Restarting in 10 seconds. Use 'shutdown /a' to cancel."
        except Exception as e:
            logger.error(f"Restart error: {e}")
            return "Failed to restart"
    
    def sleep(self) -> str:
        """Put computer to sleep."""
        try:
            # Windows
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'])
            logger.info("Sleep mode activated")
            return "Entering sleep mode"
        except Exception as e:
            logger.error(f"Sleep error: {e}")
            return "Failed to enter sleep mode"
    
    def volume_up(self) -> str:
        """Increase system volume."""
        try:
            for _ in range(5):
                pyautogui.press('volumeup')
            logger.info("Volume increased")
            return "Volume increased"
        except Exception as e:
            logger.error(f"Volume up error: {e}")
            return "Failed to increase volume"
    
    def volume_down(self) -> str:
        """Decrease system volume."""
        try:
            for _ in range(5):
                pyautogui.press('volumedown')
            logger.info("Volume decreased")
            return "Volume decreased"
        except Exception as e:
            logger.error(f"Volume down error: {e}")
            return "Failed to decrease volume"
    
    def mute(self) -> str:
        """Mute/unmute system volume."""
        try:
            pyautogui.press('volumemute')
            logger.info("Volume muted/unmuted")
            return "Volume toggled"
        except Exception as e:
            logger.error(f"Mute error: {e}")
            return "Failed to toggle mute"
    
    def get_time(self) -> str:
        """Get current time."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        return f"The time is {time_str}"
    
    def get_date(self) -> str:
        """Get current date."""
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return f"Today is {date_str}"
    
    def set_power_mode(self, mode: str) -> str:
        """
        Set laptop power mode.
        
        Args:
            mode: Power mode (performance, balanced, power_saver, custom, smart)
        
        Returns:
            Response message
        """
        mode = mode.lower().strip()
        
        # Map user-friendly names to Windows power scheme GUIDs
        power_schemes = {
            'performance': '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',  # High Performance
            'balanced': '381b4222-f694-41f0-9685-ff5bb260df2e',     # Balanced
            'custom': '381b4222-f694-41f0-9685-ff5bb260df2e',       # Balanced (alias)
            'power saver': 'a1841308-3541-4fab-bc81-f71556f20b4a',  # Power Saver
            'smart': 'a1841308-3541-4fab-bc81-f71556f20b4a',        # Power Saver (alias)
            'power_saver': 'a1841308-3541-4fab-bc81-f71556f20b4a',
        }
        
        if mode not in power_schemes:
            available = ', '.join(['performance', 'balanced/custom', 'power saver/smart'])
            return f"Unknown power mode. Available modes: {available}"
        
        try:
            scheme_guid = power_schemes[mode]
            
            # Use powercfg to set active power scheme
            result = subprocess.run(
                ['powercfg', '/setactive', scheme_guid],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Map back to friendly name
                friendly_names = {
                    'performance': 'Performance',
                    'balanced': 'Balanced',
                    'custom': 'Balanced',
                    'power saver': 'Power Saver',
                    'smart': 'Power Saver',
                    'power_saver': 'Power Saver',
                }
                friendly_name = friendly_names.get(mode, mode.title())
                
                logger.info(f"Power mode set to: {friendly_name}")
                return f"Power mode set to {friendly_name}"
            else:
                logger.error(f"Failed to set power mode: {result.stderr}")
                return "Failed to change power mode. You may need administrator privileges."
                
        except Exception as e:
            logger.error(f"Power mode error: {e}")
            return "Failed to change power mode"
    
    def get_power_mode(self) -> str:
        """
        Get current power mode.
        
        Returns:
            Current power mode description
        """
        try:
            # Get active power scheme
            result = subprocess.run(
                ['powercfg', '/getactivescheme'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                
                # Parse the output to get friendly name
                if 'High performance' in output or '8c5e7fda' in output:
                    mode = "Performance mode"
                elif 'Balanced' in output or '381b4222' in output:
                    mode = "Balanced mode"
                elif 'Power saver' in output or 'a1841308' in output:
                    mode = "Power Saver mode"
                else:
                    mode = "Custom power mode"
                
                logger.info(f"Current power mode: {mode}")
                return f"Your laptop is currently in {mode}"
            else:
                return "Unable to determine current power mode"
                
        except Exception as e:
            logger.error(f"Get power mode error: {e}")
            return "Failed to get power mode"
    
    def web_search(self, query: str) -> str:
        """
        Open web search in browser.
        
        Args:
            query: Search query
        
        Returns:
            Response message
        """
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            logger.info(f"Web search opened: {query}")
            return f"Searching for {query}"
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return "Failed to open web search"

    def type_text(self, text: str) -> str:
        """
        Type text using keyboard simulation.
        
        Args:
            text: Text to type
            
        Returns:
            Response message
        """
        try:
            import time
            logger.info(f"Starting to type: {text[:50]}...")
            
            # Give user 2 seconds to focus the right window
            time.sleep(2)
            
            pyautogui.write(text, interval=0.01)
            # Press enter after typing
            pyautogui.press('enter')
            
            logger.info("Typing complete")
            return "Text typed successfully."
        except Exception as e:
            logger.error(f"Typing error: {e}")
            return f"Failed to type text: {str(e)}"
