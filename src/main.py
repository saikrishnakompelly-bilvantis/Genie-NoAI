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

class GenieApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_first_run = False
        self.check_first_run()
        self.setup_paths()
        
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
        self.setGeometry(100, 100, 800, 700)
        self.setMinimumSize(650, 500)  # Set minimum size
        
        # Allow window to resize automatically with content
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Create web view with custom page
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
            hook_files = ['pre-commit', 'post-commit', 'scan-repo', 'pre_commit.py', 'post_commit.py', 'scan_repo.py']
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
                
                # Create a config file to store the hooks directory path and installation status
                config_file = os.path.join(genie_dir, 'config')
                with open(config_file, 'w') as f:
                    f.write(f'hooks_dir={hooks_dir}\n')
                    f.write('installed=true\n')
                
                # Show success message
                self.show_message(
                    'Installation Successful',
                    'Genie hooks have been successfully installed and configured.',
                    'success',
                    lambda: (setattr(self, 'is_first_run', False), self.load_main_ui())
                )
                
            except subprocess.CalledProcessError as e:
                self.show_message('Error', f'Failed to configure Git hooks: {str(e)}', 'error')
                return
                
        except Exception as e:
            logging.error(f"Installation failed: {str(e)}")
            self.show_message('Error', f'Failed to install hooks: {str(e)}', 'error')
            return

    def uninstall_hooks(self):
        try:
            # Remove Git configurations first
            subprocess.run(['git', 'config', '--global', '--unset', 'core.hooksPath'], 
                         check=False,  # Don't check as it might not exist
                         creationflags=subprocess.CREATE_NO_WINDOW)  # Prevent terminal window
            
            subprocess.run(['git', 'config', '--global', '--unset', 'alias.scan-repo'],
                         check=False,  # Don't check as it might not exist
                         creationflags=subprocess.CREATE_NO_WINDOW)  # Prevent terminal window
            
            # Remove .genie directory completely
            genie_dir = os.path.expanduser('~/.genie')
            if os.path.exists(genie_dir):
                import shutil
                shutil.rmtree(genie_dir)
            
            # Verify uninstallation
            if os.path.exists(genie_dir):
                raise Exception("Failed to remove .genie directory")
                
            hooks_path = subprocess.run(['git', 'config', '--global', '--get', 'core.hooksPath'],
                                      capture_output=True, 
                                      text=True,
                                      creationflags=subprocess.CREATE_NO_WINDOW).stdout.strip()
            if hooks_path:
                raise Exception("Git hooks path still set")
                
            scan_repo_alias = subprocess.run(['git', 'config', '--global', '--get', 'alias.scan-repo'],
                                           capture_output=True, 
                                           text=True,
                                           creationflags=subprocess.CREATE_NO_WINDOW).stdout.strip()
            if scan_repo_alias:
                raise Exception("Git scan-repo alias still set")
            
            self.show_message(
                'Uninstallation Complete',
                'Genie hooks have been successfully removed.',
                'success',
                lambda: (setattr(self, 'is_first_run', True), self.load_welcome_ui())
            )
            
        except Exception as e:
            self.show_message(
                'Uninstallation Failed',
                f'Unable to remove hooks:\n{str(e)}',
                'error'
            )

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
