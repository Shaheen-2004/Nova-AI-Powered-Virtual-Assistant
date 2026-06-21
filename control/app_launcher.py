"""Application launcher for NOVA."""

import subprocess
import os
from typing import Dict, Optional
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class AppLauncher:
    """Launches applications by name."""
    
    # Common application mappings for Windows
    APP_PATHS = {
        'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        'google chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        'firefox': r'C:\Program Files\Mozilla Firefox\firefox.exe',
        'edge': r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        'microsoft edge': r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe',
        'paint': 'mspaint.exe',
        'explorer': 'explorer.exe',
        'file explorer': 'explorer.exe',
        'cmd': 'cmd.exe',
        'command prompt': 'cmd.exe',
        'powershell': 'powershell.exe',
        'task manager': 'taskmgr.exe',
        'control panel': 'control.exe',
        'settings': 'ms-settings:',
        'spotify': r'C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe',
        'discord': r'C:\Users\{username}\AppData\Local\Discord\Update.exe --processStart Discord.exe',
        'vscode': r'C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe',
        'visual studio code': r'C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe',
        'brave': 'brave.exe',
        'youtube': 'https://www.youtube.com',
        'whatsapp': 'whatsapp:',
        'qbittorrent': 'qbittorrent.exe',
        'linkedin': 'https://www.linkedin.com',
    }
    
    def __init__(self):
        """Initialize app launcher."""
        self.config = Config()
        self.enabled = self.config.get('system.enable_app_launcher', True)
        
        # Replace {username} with actual username
        username = os.getenv('USERNAME', 'User')
        self.app_paths = {
            name: path.replace('{username}', username)
            for name, path in self.APP_PATHS.items()
        }
        
        # Dynamically index system apps to broaden coverage
        self._index_system_apps()
        
        logger.info(f"App launcher initialized with {len(self.app_paths)} indexed apps")

    def _index_system_apps(self):
        """Use PowerShell to find additional installed applications."""
        try:
            # Command to get Start Menu apps
            cmd = 'powershell "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json"'
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            if result:
                import json
                apps = json.loads(result)
                for app in apps:
                    name = app.get('Name', '').lower()
                    appid = app.get('AppID', '')
                    if name and appid and name not in self.app_paths:
                        # Map to shell:AppsFolder/AppID for universal launching
                        self.app_paths[name] = f"shell:AppsFolder\\{appid}"
        except Exception as e:
            logger.warning(f"Could not index system apps: {e}")
    
    def launch(self, app_name: str) -> str:
        """
        Launch an application by name.
        
        Args:
            app_name: Name of the application
        
        Returns:
            Response message
        """
        if not self.enabled:
            return "Application launching is disabled."
        
        app_name = app_name.lower().strip()
        
        # Check if app is in our mapping
        if app_name in self.app_paths:
            return self._launch_by_path(app_name, self.app_paths[app_name])
        
        # Try to launch as Windows app
        return self._launch_windows_app(app_name)
    
    def _launch_by_path(self, app_name: str, path: str) -> str:
        """
        Launch application by full path or URL.
        
        Args:
            app_name: Display name
            path: Full path or URL
        
        Returns:
            Response message
        """
        try:
            # Check if it's a URL
            if path.startswith('http'):
                import webbrowser
                webbrowser.open(path)
                logger.info(f"Opened URL: {path}")
                return f"Opening {app_name}"

            # Check if path exists (for full paths)
            if path.startswith('C:\\') and not os.path.exists(path.split()[0]):
                logger.warning(f"Application not found: {path}")
                return f"{app_name} is not installed on this system."
            
            # Launch application
            if path.startswith('ms-settings:'):
                # Windows settings URI
                subprocess.Popen(['start', path], shell=True)
            else:
                subprocess.Popen(path, shell=True)
            
            logger.info(f"Launched application: {app_name}")
            return f"Opening {app_name}"
            
        except Exception as e:
            logger.error(f"Failed to launch {app_name}: {e}")
            return f"Failed to open {app_name}"
    
    def _launch_windows_app(self, app_name: str) -> str:
        """
        Try to launch as Windows application.
        
        Args:
            app_name: Application name
        
        Returns:
            Response message
        """
        try:
            # Try to start as Windows app
            subprocess.Popen(['start', app_name], shell=True)
            logger.info(f"Attempted to launch: {app_name}")
            return f"Attempting to open {app_name}"
        except Exception as e:
            logger.error(f"Failed to launch {app_name}: {e}")
            return f"I couldn't find an application named {app_name}"
    
    def get_available_apps(self) -> list:
        """Get list of available applications."""
        return sorted(list(set(self.app_paths.keys())))
