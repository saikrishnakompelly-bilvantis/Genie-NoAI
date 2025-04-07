import sys
import os
import subprocess
import webbrowser
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QMessageBox, 
                            QFileDialog, QSplashScreen, QSizePolicy)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWebEngineCore import QWebEnginePage
from datetime import datetime
from urllib.parse import quote, urljoin
from urllib.request import pathname2url
import platform
import logging
import shutil
import time
import json

# Include our installation_tracker module
try:
    from hooks.installation_tracker import record_installation, record_uninstallation
except ImportError:
    # Handle the case where the module might not be available yet
    record_installation = record_uninstallation = lambda: None

class ReportWindow(QMainWindow):
    def __init__(self, file_path):
        super().__init__()
        self.setWindowTitle("Genie - Report Viewer")
        self.setGeometry(200, 200, 1200, 800)
        
        # Create web view
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)
        
        # Load the file directly using QUrl
        try:
            file_url = QUrl.fromLocalFile(str(file_path))
            self.web_view.setUrl(file_url)
        except Exception as e:
            print(f"Error loading report content: {e}")
            self.close()

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def javaScriptConsoleMessage(self, level, message, line, source):
        if message.startswith('action:'):
            action = message.split(':')[1]
            if action == 'install':
                self.parent.install_hooks()
            elif action == 'uninstall':
                self.parent.uninstall_hooks()
            elif action == 'exit':
                self.parent.close()
            elif action.startswith('open_report'):
                try:
                    report_index = int(message.split(':')[2])
                    if not hasattr(self.parent, 'report_paths'):
                        return
                        
                    if report_index < 0 or report_index >= len(self.parent.report_paths):
                        return
                    
                    report_path = self.parent.report_paths[report_index]
                    
                    if not os.path.exists(report_path):
                        return
                        
                    if not os.access(report_path, os.R_OK):
                        return

                    webbrowser.open('file://' + os.path.abspath(report_path))
                    
                except Exception as e:
                    pass

# Add this new function to detect restricted environments
def is_restricted_environment():
    """Detect if we're running in a restricted HSBC environment."""
    try:
        # Check command line arguments
        if len(sys.argv) > 1 and any(arg in ['--native-ui', '--hsbc'] for arg in sys.argv):
            return True
            
        # Check environment variables
        if os.environ.get('GENIE_USE_NATIVE_UI', '').lower() in ('1', 'true', 'yes'):
            return True
            
        # Check config file in user's home directory
        config_file = os.path.join(os.path.expanduser('~'), '.genie_config')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    if 'USE_NATIVE_UI=true' in content:
                        return True
            except Exception as e:
                logging.warning(f"Failed to read config file: {e}")
        
        # Check for common environment variables that might indicate an HSBC environment
        hsbc_indicators = ["CORP_", "HSBC", "ENTERPRISE_", "PROXY_REQUIRED"]
        for env_var in os.environ:
            if any(indicator in env_var for indicator in hsbc_indicators):
                return True
                
        # Try to load a simple test page to see if QWebEngineView is restricted
        from PySide6.QtWidgets import QApplication
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtCore import QUrl, QEventLoop
        
        # Skip this test if not in a GUI application
        if not QApplication.instance():
            return False
            
        test_view = QWebEngineView()
        test_view.resize(1, 1)  # Minimize size to be invisible
        
        # Create an event loop to wait for load
        loop = QEventLoop()
        test_view.loadFinished.connect(loop.quit)
        
        # Try to load a simple HTML
        test_view.setHtml("<html><body>Test</body></html>")
        
        # Wait with a timeout
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(500)  # 500ms timeout
        
        loop.exec()
        
        # Check if content loaded successfully
        if test_view.url().isEmpty():
            return True
    except Exception as e:
        # If we got an exception trying to use QWebEngineView, likely in a restricted env
        logging.warning(f"Exception when testing QWebEngineView: {e}")
        return True
        
    return False

class GenieApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_first_run = False
        self.check_first_run()
        self.setup_paths()
        
        # Check if we're in a restricted environment
        self.is_restricted_env = is_restricted_environment()
        
        # Create shortcut on first run
        if self.is_first_run:
            self.create_desktop_shortcut()
            
        self.initUI()

    def setup_paths(self):
        # Get the application's root directory
        #             # If the application is run from a Python interpreter
        self.app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Set up asset paths
        self.assets_path = os.path.join(self.app_path, 'assets')
        self.logo_path = os.path.join(self.assets_path, 'logo.png')
        
        # Set up hooks paths
        self.hooks_source = os.path.join(self.app_path, 'hooks')
        if not os.path.exists(self.hooks_source) and not getattr(sys, 'frozen', False):
            # Try to find hooks in src directory when running from source
            self.hooks_source = os.path.join(self.app_path, 'src', 'hooks')
        
        # Ensure the assets directory exists
        os.makedirs(self.assets_path, exist_ok=True)

    def initUI(self):
        self.setWindowTitle('Genie - Secret Scanning Tool')
        
        # Load SVG for window icon
        if os.path.exists(self.logo_path):
            icon = QIcon(self.logo_path)
            self.setWindowIcon(icon)
        
        # Set a smaller initial size and make window resizable
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(650, 500)  # Set minimum size
        
        # Allow window to resize automatically with content
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Create UI based on environment type
        if self.is_restricted_env:
            self.create_native_ui()
        else:
            # Original web-based UI
            self.web_view = QWebEngineView()
            self.web_page = CustomWebEnginePage(self)
            self.web_view.setPage(self.web_page)
            self.setCentralWidget(self.web_view)
            
            # Load appropriate UI
            self.load_appropriate_ui()

    def create_desktop_shortcut(self):
        """Create desktop shortcut based on the operating system."""
        try:
            # Get the path to the executable
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                if platform.system().lower() == 'darwin':
                    app_path = os.path.dirname(os.path.dirname(sys.executable))  # Get the .app bundle path
                else:
                    app_path = sys.executable
            else:
                # Running in development
                # logging.info("Not creating shortcut in development mode")
                return

            # logging.info(f"Creating desktop shortcut for: {app_path}")
            desktop_path = Path.home() / "Desktop"
            os_type = platform.system().lower()
            
            if os_type == "windows":
                try:
                    import winshell
                    from win32com.client import Dispatch
                    
                    shortcut_path = desktop_path / "Genie-Secrets.lnk"
                    shell = Dispatch('WScript.Shell')
                    shortcut = shell.CreateShortCut(str(shortcut_path))
                    shortcut.Targetpath = app_path
                    shortcut.IconLocation = f"{app_path},0"
                    shortcut.save()
                    # logging.info(f"Windows shortcut created at: {shortcut_path}")
                except ImportError:
                    # logging.error("Windows-specific modules not available")
                    pass
                    
            elif os_type == "darwin":  # macOS
                try:
                    # For macOS, create an alias to the .app bundle
                    app_path = Path(app_path)
                    if app_path.suffix == '.app' or os.path.exists(str(app_path) + '.app'):
                        if not app_path.suffix == '.app':
                            app_path = Path(str(app_path) + '.app')
                        
                        alias_script = f'''
                        tell application "Finder"
                            make new alias file to POSIX file "{app_path}" at POSIX file "{desktop_path}"
                        end tell
                        '''
                        logging.info(f"Creating macOS alias with script: {alias_script}")
                        result = subprocess.run(['osascript', '-e', alias_script], capture_output=True, text=True)
                        if result.returncode != 0:
                            logging.error(f"Error creating macOS alias: {result.stderr}")
                        else:
                            logging.info("macOS alias created successfully")
                except Exception as e:
                    logging.error(f"Error creating macOS alias: {str(e)}")
                    
            elif os_type == "linux":
                try:
                    desktop_file = desktop_path / "Genie-Secrets.desktop"
                    content = f"""[Desktop Entry]
Name=Genie-Secrets
Exec="{app_path}"
Icon={app_path}
Type=Application
Categories=Utility;Development;
"""
                    desktop_file.write_text(content)
                    os.chmod(desktop_file, 0o755)
                    # logging.info(f"Linux desktop entry created at: {desktop_file}")
                except Exception as e:
                    logging.error(f"Error creating Linux desktop entry: {str(e)}")
                    
        except Exception as e:
            # logging.error(f"Failed to create desktop shortcut: {str(e)}")
            import traceback
            # logging.error(f"Traceback: {traceback.format_exc()}")

    def check_first_run(self):
        """Check if this is the first time the application is run."""
        config_dir = os.path.expanduser('~/.genie')
        config_file = os.path.join(config_dir, 'config')
        
        # Check if config file exists and contains installation status
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config_content = f.read()
                    if 'installed=true' in config_content:
                        self.is_first_run = False
                        return
            except:
                pass
        
        # If we reach here, either:
        # - Config directory/file doesn't exist
        # - Config file doesn't have installation status
        # - There was an error reading the file
        # In all these cases, we treat it as first run
        self.is_first_run = True
        
        # Create config directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

    def load_appropriate_ui(self):
        if self.is_restricted_env:
            # For restricted environments, use appropriate native UI based on first run status
            if self.is_first_run:
                self.create_native_welcome_ui()
            else:
                self.create_native_main_ui()
            return
            
        if self.is_first_run:
            self.load_welcome_ui()
        else:
            self.load_main_ui()

    def load_welcome_ui(self):
        # First check if logo exists and convert to base64
        logo_html = ""
        if os.path.exists(self.logo_path):
            try:
                import base64
                with open(self.logo_path, 'rb') as f:
                    svg_data = f.read()
                    base64_svg = base64.b64encode(svg_data).decode('utf-8')
                    logo_html = f'<img src="data:image/svg+xml;base64,{base64_svg}" class="logo" alt="Genie Logo">'
            except Exception as e:
                print(f"Error loading logo: {e}")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Welcome to Genie</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background: #f5f5f5;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .welcome-container {{
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    padding: 2rem;
                    max-width: 600px;
                    width: 90%;
                    text-align: center;
                }}
                .logo {{
                    width: 200px;
                    height: 200px;
                    margin-bottom: 2rem;
                    object-fit: contain;
                }}
                h1 {{
                    color: #07439C;
                    font-size: 2.5rem;
                    margin: 1rem 0;
                }}
                p {{
                    color: #666;
                    font-size: 1.1rem;
                    line-height: 1.6;
                    margin: 1rem 0;
                }}
                .button-container {{
                    display: flex;
                    gap: 1rem;
                    justify-content: center;
                    margin-top: 2rem;
                }}
                .install-btn {{
                    background-color: #07439C;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 1rem 2rem;
                    font-size: 1.2rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                .exit-btn {{
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 1rem 2rem;
                    font-size: 1.2rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                .install-btn:hover, .exit-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                }}
                .install-btn:hover {{
                    background-color: #053278;
                }}
                .exit-btn:hover {{
                    background-color: #5a6268;
                }}
            </style>
        </head>
        <body>
            <div class="welcome-container">
                {logo_html}
                <h1>Welcome to Genie</h1>
                <p>Genie helps enforce HSBC's coding guidelines by preventing credentials and secrets from being committed to your Git repositories.</p>
                <p>To get started, click the button below to install Genie's Git hooks.</p>
                <div class="button-container">
                    <button class="install-btn" onclick="console.log('action:install')">Install Hooks</button>
                    <button class="exit-btn" onclick="console.log('action:exit')">Exit</button>
                </div>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(html_content)

    def load_main_ui(self):
        # Load SVG content for header logo
        logo_html = ""
        if os.path.exists(self.logo_path):
            try:
                import base64
                with open(self.logo_path, 'rb') as f:
                    svg_data = f.read()
                    base64_svg = base64.b64encode(svg_data).decode('utf-8')
                    logo_html = f'<img src="data:image/svg+xml;base64,{base64_svg}" class="logo" alt="Genie Logo">'
            except Exception as e:
                print(f"Error loading logo: {e}")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Genie - Secret Scanning Tool</title>
            <script>
                function handleReportClick(index) {{
                    console.log('action:open_report:' + index);
                }}
            </script>
            <style>
                body {{
                    font-family: -apple-system, system-ui, sans-serif;
                    margin: 20px;
                    background: #f5f5f5;
                }}
                .header {{
                    display: flex;
                    align-items: center;
                    margin-bottom: 2rem;
                    padding: 1rem;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                .logo {{
                    width: 40px;
                    height: 40px;
                    margin-right: 1rem;
                }}
                .header-text {{
                    flex-grow: 1;
                }}
                h1, h2 {{
                    color: #07439C;
                    margin: 0;
                }}
                h1 {{
                    font-size: 1.5rem;
                }}
                h2 {{
                    font-size: 1.3rem;
                    margin: 1.5rem 0 1rem 0;
                }}
                .subtitle {{
                    color: #666;
                    margin: 0.5rem 0 0 0;
                    font-size: 0.9rem;
                }}
                .button-container {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 1rem;
                    margin-bottom: 2rem;
                }}
                .action-btn {{
                    background-color: #07439C;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 1rem;
                    font-size: 1rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                .action-btn:hover {{
                    background-color: #053278;
                }}
                .uninstall-btn {{
                    background-color: #dc3545;
                }}
                .uninstall-btn:hover {{
                    background-color: #c82333;
                }}
                .exit-btn {{
                    background-color: #6c757d;
                }}
                .exit-btn:hover {{
                    background-color: #5a6268;
                }}
                .usage-section {{
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    padding: 1.5rem;
                    margin-top: 1.5rem;
                }}
                .usage-steps {{
                    margin-top: 1rem;
                }}
                .step {{
                    background: #f8f9fa;
                    border-left: 4px solid #07439C;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    border-radius: 0 8px 8px 0;
                }}
                .step-header {{
                    font-weight: 600;
                    color: #07439C;
                    margin-bottom: 0.5rem;
                }}
                .step-content {{
                    color: #555;
                    line-height: 1.5;
                }}
                code {{
                    background: #e9ecef;
                    padding: 0.2rem 0.4rem;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 0.9rem;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                {logo_html}
                <div class="header-text">
                    <h1>Genie - Secret Scanning Tool</h1>
                    <p class="subtitle">Enhance your Git workflow with powerful hooks</p>
                </div>
            </div>
            <div class="main-container">
                <div class="button-container">
                    <button class="action-btn uninstall-btn" onclick="console.log('action:uninstall')">Uninstall Hooks</button>
                    <button class="action-btn exit-btn" onclick="console.log('action:exit')">Exit</button>
                </div>
                
                <div class="usage-section">
                    <h2>How Genie Works</h2>
                    <div class="tip">
                        <p>Genie enhances your Git workflow by:</p>
                        <ul>
                            <li>Automatically scanning code for secrets during commits</li>
                            <li>Prompting for justification when secrets are detected</li>
                            <li>Adding justifications to commit messages</li>
                            <li>Generating HTML reports of scan results</li>
                            <li>Working with standard Git commands from any terminal</li>
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        print("Debug: Setting HTML content")
        self.web_view.setHtml(html_content)

    def show_message(self, title, message, type='info', callback=None):
        # Get the appropriate icon based on message type
        icon_map = {
            'info': '🔔',
            'error': '⚠️',
            'success': '✨'
        }
        icon = icon_map.get(type, '🔔')  # Default to info icon if type not found
        
        # Get the appropriate button text
        button_text = 'OK'
        if type == 'error':
            button_text = 'Back'
        elif type == 'success':
            button_text = 'Continue'

        # Get the appropriate button color
        button_color = '#07439C'  # Default blue color
        if type == 'error':
            button_color = '#dc3545'  # Red for error

        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                :root {{
                    --primary-color: #07439C;
                    --error-color: #dc3545;
                    --bg-color: #f5f5f5;
                    --text-color: #333;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: var(--bg-color);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: calc(100vh - 40px);
                }}
                
                .message-container {{
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    padding: 2rem;
                    max-width: 500px;
                    width: 100%;
                    text-align: center;
                }}
                
                .icon {{
                    font-size: 48px;
                    margin-bottom: 1rem;
                    display: inline-block;
                    animation: bounceIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                }}
                
                @keyframes bounceIn {{
                    0% {{ transform: scale(0); }}
                    50% {{ transform: scale(1.2); }}
                    100% {{ transform: scale(1); }}
                }}
                
                .title {{
                    color: {button_color};
                    font-size: 24px;
                    font-weight: 600;
                    margin: 1rem 0;
                }}
                
                .message {{
                    color: var(--text-color);
                    font-size: 16px;
                    line-height: 1.6;
                    margin: 1rem 0;
                    padding: 0 1rem;
                }}
                
                .button {{
                    background-color: {button_color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 32px;
                    font-size: 16px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: transform 0.2s, box-shadow 0.2s;
                    margin-top: 1rem;
                }}
                
                .button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                    background-color: {button_color_hover};
                }}
                
                .button:active {{
                    transform: translateY(0);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
            </style>
        </head>
        <body>
            <div class="message-container">
                <div class="icon" role="img" aria-label="{type} icon">
                    {icon}
                </div>
                <div class="title">{title}</div>
                <div class="message">
                    {message}
                </div>
                <button class="button" onclick="console.log('action:message_ok')">
                    {button_text}
                </button>
            </div>
            <script>
                // Enable clicking anywhere or pressing Enter/Space to dismiss
                document.addEventListener('keydown', function(e) {{
                    if (e.key === 'Enter' || e.key === ' ') {{
                        console.log('action:message_ok');
                    }}
                }});
            </script>
        </body>
        </html>
        """.format(
            title=title,
            button_color=button_color,
            button_color_hover=button_color if type == 'error' else '#053278',
            icon=icon,
            message=message.replace('\n', '<br>'),
            button_text=button_text,
            type=type  # Add this line to pass the type parameter
        )

        # Update message handler
        original_handler = self.web_page.javaScriptConsoleMessage
        def message_handler(level, msg, line, source):
            if msg == 'action:message_ok' and callback:
                callback()
            else:
                original_handler(level, msg, line, source)
        self.web_page.javaScriptConsoleMessage = message_handler

        # Display the message
        self.web_view.setHtml(html_content)
        self._message_callback = callback

    def get_hooks_path(self):
        """Get the correct hooks path whether running from source or frozen executable."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            if platform.system().lower() == 'darwin':
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(sys._MEIPASS)
            return base_path / 'hooks'
        else:
            # Running in development
            return Path(__file__).parent / 'hooks'

    def install_hooks(self):
        """Install Git hooks and necessary files."""
        try:
            # Get the user's home directory
            home_dir = os.path.expanduser('~')
            genie_dir = os.path.join(home_dir, '.genie')
            hooks_dir = os.path.join(genie_dir, 'hooks')
            
            # Create necessary directories
            os.makedirs(hooks_dir, exist_ok=True)
            
            # Get the correct hooks source directory using get_hooks_path
            hooks_source = self.get_hooks_path()
            
            # Log paths for debugging
            logging.info(f"Hooks source directory: {hooks_source}")
            logging.info(f"Hooks target directory: {hooks_dir}")
            
            if not hooks_source.exists():
                raise FileNotFoundError(f"Hooks source directory not found: {hooks_source}")
            
            # Copy hook files
            hook_files = ['pre-push','pre_push.py']
            for hook_file in hook_files:
                source_file = hooks_source / hook_file
                target_file = Path(hooks_dir) / hook_file
                
                if source_file.exists():
                    shutil.copy2(str(source_file), str(target_file))
                    # Make the file executable
                    os.chmod(str(target_file), 0o755)
                    logging.info(f"Copied hook file: {source_file} -> {target_file}")
                else:
                    raise FileNotFoundError(f"Hook file not found: {source_file}")
            
            # Copy commit_scripts directory if it exists
            commit_scripts_dir = hooks_source / 'commit_scripts'
            if commit_scripts_dir.exists():
                target_scripts_dir = Path(hooks_dir) / 'commit_scripts'
                shutil.copytree(str(commit_scripts_dir), str(target_scripts_dir), dirs_exist_ok=True)
                logging.info(f"Copied commit_scripts directory: {commit_scripts_dir} -> {target_scripts_dir}")
            
            # Set up Git configuration
            try:
                # Platform-specific subprocess calls
                if platform.system().lower() == 'windows':
                    # Windows-specific code with creationflags
                    # Remove any existing Git hooks configuration
                    subprocess.run(['git', 'config', '--global', '--unset', 'core.hooksPath'], 
                                check=False,  # Don't check as it might not exist
                                creationflags=subprocess.CREATE_NO_WINDOW)  # Prevent terminal window
                    subprocess.run(['git', 'config', '--global', '--unset', 'alias.scan-repo'],
                                check=False,  # Don't check as it might not exist
                                creationflags=subprocess.CREATE_NO_WINDOW)  # Prevent terminal window
                    
                    # Set up new Git hooks configuration
                    subprocess.run(['git', 'config', '--global', 'core.hooksPath', hooks_dir], 
                                check=True,
                                creationflags=subprocess.CREATE_NO_WINDOW)  # Prevent terminal window
                    
                    # Create git alias for scan-repo with absolute path
                    scan_repo_path = os.path.join(hooks_dir, 'scan-repo')
                    alias_cmd = f'!bash "{scan_repo_path}"'
                    subprocess.run(['git', 'config', '--global', 'alias.scan-repo', alias_cmd], 
                                check=True,
                                creationflags=subprocess.CREATE_NO_WINDOW)  # Prevent terminal window
                else:
                    # macOS/Linux code without creationflags
                    # Remove any existing Git hooks configuration
                    subprocess.run(['git', 'config', '--global', '--unset', 'core.hooksPath'], 
                                check=False)  # Don't check as it might not exist
                    subprocess.run(['git', 'config', '--global', '--unset', 'alias.scan-repo'],
                                check=False)  # Don't check as it might not exist
                    
                    # Set up new Git hooks configuration
                    subprocess.run(['git', 'config', '--global', 'core.hooksPath', hooks_dir], 
                                check=True)
                    
                    # Create git alias for scan-repo with absolute path
                    scan_repo_path = os.path.join(hooks_dir, 'scan-repo')
                    alias_cmd = f'!bash "{scan_repo_path}"'
                    subprocess.run(['git', 'config', '--global', 'alias.scan-repo', alias_cmd], 
                                check=True)
                
                # Create a config file to store the hooks directory path and installation status
                config_file = os.path.join(genie_dir, 'config')
                with open(config_file, 'w') as f:
                    f.write(f'hooks_dir={hooks_dir}\n')
                    f.write('installed=true\n')
                
                # Record installation in CSV and push to GitHub
                try:
                    # Import here in case the module wasn't available at startup
                    from hooks.installation_tracker import record_installation
                    record_installation()
                    logging.info("Installation recorded in tracking CSV")
                except Exception as e:
                    logging.warning(f"Could not record installation: {e}")
                
                # Handle successful installation based on UI mode
                if self.is_restricted_env:
                    # For HSBC mode with native UI
                    self.is_first_run = False
                    self.create_native_main_ui()
                    
                    # Update status
                    if hasattr(self, 'status_label'):
                        self.status_label.setText("Hooks installed successfully!")
                else:
                    # For standard web-based UI
                    self.show_message(
                        'Installation Successful',
                        'Genie hooks have been successfully installed and configured.',
                        'success',
                        lambda: (setattr(self, 'is_first_run', False), self.load_main_ui())
                    )
                
            except subprocess.CalledProcessError as e:
                if self.is_restricted_env:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", f"Failed to configure Git hooks: {str(e)}")
                else:
                    self.show_message('Error', f'Failed to configure Git hooks: {str(e)}', 'error')
                return
                
        except Exception as e:
            logging.error(f"Installation failed: {str(e)}")
            if self.is_restricted_env:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to install hooks: {str(e)}")
            else:
                self.show_message('Error', f'Failed to install hooks: {str(e)}', 'error')
            return

    def uninstall_hooks(self):
        try:
            # Remove Git configurations first
            if platform.system().lower() == 'windows':
                subprocess.run(['git', 'config', '--global', '--unset', 'core.hooksPath'], 
                            check=False,  # Don't check as it might not exist
                            creationflags=subprocess.CREATE_NO_WINDOW)  # Prevent terminal window
                
                subprocess.run(['git', 'config', '--global', '--unset', 'alias.scan-repo'],
                            check=False,  # Don't check as it might not exist
                            creationflags=subprocess.CREATE_NO_WINDOW)  # Prevent terminal window
            else:
                # Non-Windows platforms don't have creationflags
                subprocess.run(['git', 'config', '--global', '--unset', 'core.hooksPath'], 
                            check=False)  # Don't check as it might not exist
                
                subprocess.run(['git', 'config', '--global', '--unset', 'alias.scan-repo'],
                            check=False)  # Don't check as it might not exist
            
            # Record uninstallation before removing the directory
            try:
                # Import here in case the module wasn't available at startup
                from hooks.installation_tracker import record_uninstallation
                record_uninstallation()
                logging.info("Uninstallation recorded in tracking CSV")
            except Exception as e:
                logging.warning(f"Could not record uninstallation: {e}")
            
            # Remove .genie directory completely
            genie_dir = os.path.expanduser('~/.genie')
            if os.path.exists(genie_dir):
                import shutil
                shutil.rmtree(genie_dir)
            
            # Verify uninstallation
            if os.path.exists(genie_dir):
                raise Exception("Failed to remove .genie directory")
                
            if platform.system().lower() == 'windows':
                hooks_path = subprocess.run(['git', 'config', '--global', '--get', 'core.hooksPath'],
                                        capture_output=True, 
                                        text=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW).stdout.strip()
                
                scan_repo_alias = subprocess.run(['git', 'config', '--global', '--get', 'alias.scan-repo'],
                                            capture_output=True, 
                                            text=True,
                                            creationflags=subprocess.CREATE_NO_WINDOW).stdout.strip()
            else:
                hooks_path = subprocess.run(['git', 'config', '--global', '--get', 'core.hooksPath'],
                                        capture_output=True, 
                                        text=True).stdout.strip()
                
                scan_repo_alias = subprocess.run(['git', 'config', '--global', '--get', 'alias.scan-repo'],
                                            capture_output=True, 
                                            text=True).stdout.strip()
            
            if hooks_path:
                raise Exception("Git hooks path still set")
                
            if scan_repo_alias:
                raise Exception("Git scan-repo alias still set")
            
            # Handle success based on UI mode
            if self.is_restricted_env:
                # For HSBC mode with native UI
                self.is_first_run = True
                self.create_native_welcome_ui()
                
                # Update status
                if hasattr(self, 'status_label'):
                    self.status_label.setText("Hooks uninstalled successfully!")
            else:
                # For standard web-based UI
                self.show_message(
                    'Uninstallation Complete',
                    'Genie hooks have been successfully removed.',
                    'success',
                    lambda: (setattr(self, 'is_first_run', True), self.load_welcome_ui())
                )
            
        except Exception as e:
            if self.is_restricted_env:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Uninstallation Failed", f"Unable to remove hooks:\n{str(e)}")
            else:
                self.show_message(
                    'Uninstallation Failed',
                    f'Unable to remove hooks:\n{str(e)}',
                    'error'
                )

    def create_native_welcome_ui(self):
        """Create a fallback native UI for HSBC environments - first run welcome screen."""
        from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, 
                                    QLabel, QWidget, QTextBrowser, QToolBar, QSizePolicy)
        
        # Main container widget
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(30, 30, 30, 30)  # Increased margins
        
        # Add logo at top
        if os.path.exists(self.logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(self.logo_path)
            scaled_pixmap = pixmap.scaledToWidth(150)  # Increased logo size
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(logo_label)
        
        # Add title
        title_label = QLabel("Welcome to Genie")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #07439C; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Info text
        info_text = QTextBrowser()
        info_text.setOpenExternalLinks(True)
        info_text.setMaximumHeight(200)  # Increased height
        info_text.setHtml("""
        <div style='margin: 15px;'>
            <h3>Secret Scanning Tool</h3>
            <p>Genie helps you avoid committing secrets and credentials to your Git repositories.</p>
            <p>To get started, click the button below to install Genie's Git hooks.</p>
        </div>
        """)
        main_layout.addWidget(info_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 10)  # Increased margins
        
        install_btn = QPushButton("Install Hooks")
        install_btn.setMinimumHeight(40)  # Increased button height
        install_btn.setStyleSheet("""
            QPushButton {
                background-color: #07439C;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #053278;
            }
        """)
        install_btn.clicked.connect(self.install_hooks)
        
        exit_btn = QPushButton("Exit")
        exit_btn.setMinimumHeight(40)  # Increased button height
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        exit_btn.clicked.connect(self.close)
        
        button_layout.addWidget(install_btn)
        button_layout.addWidget(exit_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status label at bottom
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic; font-size: 12px;")
        main_layout.addWidget(self.status_label)
        
        # Set the central widget
        self.setCentralWidget(container)
        
        # Set fixed window size to fit content
        self.setFixedSize(500, 500)  # Increased window size
        self.setMinimumSize(500, 500)  # Ensure minimum size

    def create_native_main_ui(self):
        """Create a fallback native UI for HSBC environments - main screen after installation."""
        from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, 
                                    QLabel, QWidget, QTextBrowser, QToolBar, QSizePolicy)
        
        # Main container widget
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(30, 30, 30, 30)  # Increased margins
        
        # Add logo at top
        if os.path.exists(self.logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(self.logo_path)
            scaled_pixmap = pixmap.scaledToWidth(120)  # Increased logo size
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(logo_label)
        
        # Add title
        title_label = QLabel("Genie - Secret Scanning Tool")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #07439C; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Info text
        info_text = QTextBrowser()
        info_text.setOpenExternalLinks(True)
        info_text.setMaximumHeight(250)  # Increased height
        info_text.setHtml("""
        <div style='margin: 15px;'>
            <h3>Hooks Installed Successfully</h3>
            <p>Genie is now monitoring your Git commits for secrets and credentials.</p>
            <h4>How Genie Works:</h4>
            <ul>
                <li>Automatically scans code for secrets during commits</li>
                <li>Prompts for justification when secrets are detected</li>
                <li>Generates HTML reports of scan results</li>
                <li>Works with standard Git commands from any terminal</li>
            </ul>
        </div>
        """)
        main_layout.addWidget(info_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 10)  # Increased margins
        
        uninstall_btn = QPushButton("Uninstall Hooks")
        uninstall_btn.setMinimumHeight(40)  # Increased button height
        uninstall_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        uninstall_btn.clicked.connect(self.uninstall_hooks)
        
        exit_btn = QPushButton("Exit")
        exit_btn.setMinimumHeight(40)  # Increased button height
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        exit_btn.clicked.connect(self.close)
        
        button_layout.addWidget(uninstall_btn)
        button_layout.addWidget(exit_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status label at bottom
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic; font-size: 12px;")
        main_layout.addWidget(self.status_label)
        
        # Set the central widget
        self.setCentralWidget(container)
        
        # Set fixed window size to fit content
        self.setFixedSize(500, 550)  # Increased window size
        self.setMinimumSize(500, 550)  # Ensure minimum size

    def create_native_ui(self):
        """Select the appropriate native UI based on first run status."""
        if self.is_first_run:
            self.create_native_welcome_ui()
        else:
            self.create_native_main_ui()

    def select_repo_and_scan(self):
        """Select a Git repository and scan it for secrets."""
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            
            # Show directory selection dialog
            repo_path = QFileDialog.getExistingDirectory(
                self,
                "Select Git Repository",
                os.path.expanduser("~"),
                QFileDialog.ShowDirsOnly
            )
            
            if not repo_path:
                # User canceled
                return
                
            # Check if selected directory is a Git repository
            if not os.path.isdir(os.path.join(repo_path, '.git')):
                QMessageBox.warning(
                    self,
                    "Invalid Repository",
                    "The selected directory is not a Git repository.\nPlease select a valid Git repository."
                )
                return
                
            # Update status if using native UI
            if hasattr(self, 'status_label'):
                self.status_label.setText("Scanning repository...")
                self.status_label.repaint()  # Force update
                
            # Prepare scan command
            scan_script = None
            
            # Check if we have hooks installed
            hooks_dir = os.path.expanduser('~/.genie/hooks')
            if os.path.exists(os.path.join(hooks_dir, 'scan_repo.py')):
                scan_script = os.path.join(hooks_dir, 'scan_repo.py')
            else:
                # Try to find in hooks source
                if hasattr(self, 'hooks_source'):
                    scan_script = os.path.join(self.hooks_source, 'scan_repo.py')
                    
            if not scan_script or not os.path.exists(scan_script):
                QMessageBox.critical(
                    self,
                    "Scan Failed",
                    "Could not find scan_repo.py script.\nPlease install hooks first."
                )
                return
                
            # Create a temporary directory for the report
            import tempfile
            report_dir = os.path.join(tempfile.gettempdir(), 'genie_reports')
            os.makedirs(report_dir, exist_ok=True)
            
            # Run the scan
            original_dir = os.getcwd()
            try:
                # Change to the repository directory
                os.chdir(repo_path)
                
                # Execute the scan
                cmd = [sys.executable, scan_script]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Check for errors
                if result.returncode != 0:
                    error_msg = result.stderr or "Unknown error occurred during scan."
                    QMessageBox.critical(self, "Scan Failed", f"Error scanning repository:\n{error_msg}")
                    return
                    
                # Look for the generated report
                report_path = None
                for line in result.stdout.split('\n'):
                    if 'Report saved to:' in line:
                        report_path = line.split('Report saved to:')[1].strip()
                        break
                
                if not report_path or not os.path.exists(report_path):
                    # Try to find the latest report in the .commit-reports directory
                    reports_dir = os.path.join(repo_path, '.git', 'hooks', '.commit-reports')
                    
                    if os.path.exists(reports_dir):
                        # Get the latest report
                        reports = sorted(
                            [os.path.join(reports_dir, f) for f in os.listdir(reports_dir) if f.endswith('.html')],
                            key=os.path.getmtime,
                            reverse=True
                        )
                        
                        if reports:
                            report_path = reports[0]
                
                # Open the report
                if report_path and os.path.exists(report_path):
                    webbrowser.open('file://' + os.path.abspath(report_path))
                    
                    # Update status
                    if hasattr(self, 'status_label'):
                        self.status_label.setText("Scan complete. Report opened in browser.")
                else:
                    # Couldn't find a report - show the raw output
                    QMessageBox.information(
                        self,
                        "Scan Complete",
                        f"Scan completed but no report was found.\n\nOutput:\n{result.stdout}"
                    )
            except Exception as e:
                QMessageBox.critical(self, "Scan Failed", f"Error scanning repository:\n{str(e)}")
            finally:
                # Restore original directory
                os.chdir(original_dir)
                
                # Update status
                if hasattr(self, 'status_label'):
                    self.status_label.setText("Ready")
                    
        except Exception as e:
            # Show error
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to scan repository:\n{str(e)}")

if __name__ == '__main__':
    try:
        # Initialize QApplication first
        app = QApplication(sys.argv)
        
        # Set application style to ensure consistent GUI appearance
        app.setStyle('Fusion')
        
        # Get application path
        if getattr(sys, 'frozen', False):
            app_path = sys._MEIPASS
        else:
            app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Get the logo path
        logo_path = os.path.join(app_path, 'assets', 'logo.png')
        
        # Show splash screen with logo if it exists
        splash = None
        if os.path.exists(logo_path):
            splash_pix = QPixmap(logo_path)
            if not splash_pix.isNull():
                splash = QSplashScreen(splash_pix)
                splash.show()
        
        # Initialize main window
        main = GenieApp()
        main.show()
        
        # Finish splash screen if it was shown
        if splash:
            splash.finish(main)
        
        # Start event loop
        exit_code = app.exec()
        sys.exit(exit_code)
        
    except Exception as e:
        # Show error in GUI if possible
        try:
            if 'app' in locals():
                QMessageBox.critical(None, "Fatal Error",
                    f"A fatal error occurred:\n\n{str(e)}")
        except:
            pass
        
        sys.exit(1)
