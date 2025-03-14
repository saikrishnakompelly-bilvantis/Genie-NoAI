import sys
import os
import subprocess
import webbrowser
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox, 
                            QFileDialog, QSplashScreen)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWebEngineCore import QWebEnginePage
from datetime import datetime
from urllib.parse import quote, urljoin
from urllib.request import pathname2url
import platform
import logging

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
            elif action == 'scan':
                self.parent.scan_repository()
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
        
        self.setGeometry(100, 100, 1000, 600)

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
                <p>Genie is your trusted companion for scanning Git repositories and ensuring code security. 
                   With powerful secret detection and file scanning capabilities, Genie helps keep your repositories clean and secure.</p>
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

        # Get list of scan reports
        reports_dir = os.path.expanduser('~/.genie/hooks/.reports')
        reports_list = ""

        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)

        if os.path.exists(reports_dir):
            reports = sorted(
                [f for f in os.listdir(reports_dir) if f.startswith('scan_report_') and f.endswith('.html')],
                reverse=True
            )
            
            if reports:
                reports_list = """
                    <div class="reports-section">
                        <h2>Scan History</h2>
                        <div class="reports-list">
                """
                for i, report in enumerate(reports):
                    timestamp = report.replace('scan_report_', '').replace('.html', '')
                    try:
                        date_obj = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                        formatted_date = date_obj.strftime('%B %d, %Y at %I:%M %p')
                    except:
                        formatted_date = timestamp

                    report_path = os.path.join(reports_dir, report)
                    reports_list += f"""
                        <div class="report-item" onclick="handleReportClick({i})" style="cursor: pointer;">
                            <div class="report-icon">📄</div>
                            <div class="report-info">
                                <div class="report-date">{formatted_date}</div>
                                <div class="report-name">{report}</div>
                            </div>
                        </div>
                    """
                reports_list += """
                        </div>
                    </div>
                """
                self.report_paths = [os.path.join(reports_dir, report) for report in reports]
            else:
                reports_list = """
                    <div class="reports-section">
                        <h2>Scan History</h2>
                        <div class="empty-state">
                            <p>No scan reports available yet. Click "Scan Repository" to create one.</p>
                        </div>
                    </div>
                """

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
                    font-size: 1.2rem;
                    margin-bottom: 1rem;
                }}
                .subtitle {{
                    color: #666;
                    margin: 0.5rem 0 0 0;
                    font-size: 0.9rem;
                }}
                .button-container {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
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
                .reports-section {{
                    margin-top: 1rem;
                    background: white;
                    padding: 1.5rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                .reports-list {{
                    display: grid;
                    gap: 1rem;
                }}
                .empty-state {{
                    text-align: center;
                    color: #666;
                    padding: 2rem;
                    background: #f8f9fa;
                    border-radius: 8px;
                }}
                .report-item {{
                    display: flex;
                    align-items: center;
                    padding: 1rem;
                    background: #f8f9fa;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    -webkit-user-select: none;
                    -moz-user-select: none;
                    -ms-user-select: none;
                    user-select: none;
                }}
                .report-item:hover {{
                    background: #e9ecef;
                    transform: translateX(5px);
                }}
                .report-item:active {{
                    background: #dee2e6;
                    transform: translateX(2px);
                }}
                .report-icon {{
                    font-size: 1.5rem;
                    margin-right: 1rem;
                    color: #07439C;
                }}
                .report-info {{
                    flex-grow: 1;
                }}
                .report-date {{
                    font-weight: 500;
                    color: #07439C;
                }}
                .report-name {{
                    font-size: 0.8rem;
                    color: #718096;
                    margin-top: 0.25rem;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                {logo_html}
                <div class="header-text">
                    <h1>Genie - Secret Scanning Tool</h1>
                    <p class="subtitle">Secure your repositories with advanced secret detection</p>
                </div>
            </div>
            <div class="main-container">
                <div class="button-container">
                    <button class="action-btn" onclick="console.log('action:scan')">Scan Repository</button>
                    <button class="action-btn uninstall-btn" onclick="console.log('action:uninstall')">Uninstall Hooks</button>
                    <button class="action-btn exit-btn" onclick="console.log('action:exit')">Exit</button>
                </div>
                {reports_list}
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
                base_path = Path(sys.executable).parent
            return base_path / 'hooks'
        else:
            # Running in development
            return Path(__file__).parent / 'hooks'

    def install_hooks(self):
        """Install Git hooks and necessary files."""
        try:
            # Get user's home directory
            home_dir = os.path.expanduser('~')
            genie_dir = os.path.join(home_dir, '.genie')
            hooks_dir = os.path.join(genie_dir, 'hooks')
            
            # Clean up any existing installation first
            if os.path.exists(genie_dir):
                import shutil
                shutil.rmtree(genie_dir)
            
            # Create genie directory
            os.makedirs(genie_dir, exist_ok=True)
            
            # Get the source hooks directory
            hooks_source = self.get_hooks_path()
            if not hooks_source.exists():
                raise FileNotFoundError(f"Hooks directory not found at {hooks_source}")
            
            # Copy entire hooks directory structure
            import shutil
            shutil.copytree(hooks_source, hooks_dir)
            
            # Make hook files executable
            hook_files = ['scan-repo', 'pre-commit', 'post-commit']
            for hook in hook_files:
                hook_path = os.path.join(hooks_dir, hook)
                if os.path.exists(hook_path):
                    os.chmod(hook_path, 0o755)
            
            # Set up Git configuration
            try:
                # Remove any existing Git hooks configuration
                subprocess.run(['git', 'config', '--global', '--unset', 'core.hooksPath'], 
                             check=False)  # Don't check as it might not exist
                subprocess.run(['git', 'config', '--global', '--unset', 'alias.scan-repo'],
                             check=False)  # Don't check as it might not exist
                
                # Set up new Git hooks configuration
                subprocess.run(['git', 'config', '--global', 'core.hooksPath', hooks_dir], check=True)
                
                # Create git alias for scan-repo with absolute path
                scan_repo_path = os.path.join(hooks_dir, 'scan-repo')
                alias_cmd = f'!bash "{scan_repo_path}"'
                subprocess.run(['git', 'config', '--global', 'alias.scan-repo', alias_cmd], check=True)
                
                # Create a config file to store the hooks directory path and installation status
                config_file = os.path.join(genie_dir, 'config')
                with open(config_file, 'w') as f:
                    f.write(f'hooks_dir={hooks_dir}\n')
                    f.write('installed=true\n')
                
                # Show success message with custom HTML
                success_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                            margin: 0;
                            padding: 2rem;
                            background: #f5f5f5;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: calc(100vh - 4rem);
                        }}
                        .success-container {{
                            background: white;
                            border-radius: 16px;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            padding: 2rem;
                            max-width: 600px;
                            width: 90%;
                            text-align: center;
                        }}
                        .success-icon {{
                            color: #28a745;
                            font-size: 4rem;
                            margin-bottom: 1rem;
                        }}
                        h1 {{
                            color: #07439C;
                            font-size: 2rem;
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
                        .scan-btn {{
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
                        .scan-btn:hover {{
                            background-color: #053278;
                            transform: translateY(-2px);
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                        }}
                    </style>
                </head>
                <body>
                    <div class="success-container">
                        <div class="success-icon">✓</div>
                        <h1>Installation Successful!</h1>
                        <p>Genie has been successfully installed and configured. Your Git hooks are now set up and ready to use.</p>
                        <p>Installation path: {hooks_dir}</p>
                        <div class="button-container">
                            <button class="scan-btn" onclick="console.log('action:scan')">Start Scanning</button>
                        </div>
                    </div>
                </body>
                </html>
                """
                self.web_view.setHtml(success_html)
                
                # Update the UI based on installation status
                self.is_first_run = False
                self.load_main_ui()
                
            except subprocess.CalledProcessError as e:
                self.show_message('Error', f'Failed to configure Git hooks: {str(e)}', 'error')
                return
                
        except Exception as e:
            self.show_message('Error', f'Failed to install hooks: {str(e)}', 'error')
            return

    def uninstall_hooks(self):
        try:
            # Remove Git configurations first
            subprocess.run(['git', 'config', '--global', '--unset', 'core.hooksPath'], 
                         check=False)  # Don't check as it might not exist
            
            subprocess.run(['git', 'config', '--global', '--unset', 'alias.scan-repo'],
                         check=False)  # Don't check as it might not exist
            
            # Remove .genie directory completely
            genie_dir = os.path.expanduser('~/.genie')
            if os.path.exists(genie_dir):
                import shutil
                shutil.rmtree(genie_dir)
            
            # Verify uninstallation
            if os.path.exists(genie_dir):
                raise Exception("Failed to remove .genie directory")
                
            hooks_path = subprocess.run(['git', 'config', '--global', '--get', 'core.hooksPath'],
                                      capture_output=True, text=True).stdout.strip()
            if hooks_path:
                raise Exception("Git hooks path still set")
                
            scan_repo_alias = subprocess.run(['git', 'config', '--global', '--get', 'alias.scan-repo'],
                                           capture_output=True, text=True).stdout.strip()
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

    def scan_repository(self):
        # Create HTML for folder selection
        folder_selection_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Select Repository</title>
            <script>
                function handleBack() {
                    console.log('action:back');
                }
            </script>
            <style>
                body {
                    font-family: -apple-system, system-ui, sans-serif;
                    margin: 20px;
                    background: #f5f5f5;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }
                .container {
                    max-width: 800px;
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }
                h2 {
                    color: #07439C;
                    margin-bottom: 20px;
                }
                .selected-path {
                    margin: 20px 0;
                    padding: 10px;
                    background: #f8f9fa;
                    border-radius: 4px;
                    word-break: break-all;
                }
                button {
                    padding: 10px 20px;
                    margin: 10px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background-color 0.3s;
                }
                .browse-btn {
                    background-color: #07439C;
                    color: white;
                }
                .browse-btn:hover {
                    background-color: #053278;
                }
                .scan-btn {
                    background-color: #07439C;
                    color: white;
                }
                .scan-btn:hover {
                    background-color: #053278;
                }
                .back-btn {
                    background-color: #6c757d;
                    color: white;
                }
                .back-btn:hover {
                    background-color: #5a6268;
                }
                #selectedPath {
                    color: #666;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Select Repository to Scan</h2>
                <div>
                    <button class="browse-btn" onclick="console.log('action:browse')">Browse Repository</button>
                </div>
                <div class="selected-path">
                    <p>Selected Path:</p>
                    <p id="selectedPath">No repository selected</p>
                </div>
                <div>
                    <button class="scan-btn" onclick="console.log('action:start_scan')" id="scanButton" disabled>Start Scan</button>
                    <button class="back-btn" onclick="handleBack()">Back</button>
                </div>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(folder_selection_html)
        self.selected_repo_path = None

        # Update the CustomWebEnginePage class to handle new actions
        def handle_browse():
            repo_path = QFileDialog.getExistingDirectory(self, 'Select Git Repository')
            if repo_path:
                self.selected_repo_path = repo_path
                self.web_view.page().runJavaScript(
                    f"document.getElementById('selectedPath').textContent = '{repo_path}';"
                    f"document.getElementById('scanButton').disabled = false;"
                )

        def handle_start_scan():
            if self.selected_repo_path:
                try:
                    current_dir = os.getcwd()
                    os.chdir(self.selected_repo_path)
                    
                    # Check if it's a git repository
                    try:
                        subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], 
                                    check=True, capture_output=True)
                    except subprocess.CalledProcessError:
                        raise Exception("The selected directory is not a Git repository")
                    
                    # Run the scan using the git scan-repo command
                    result = subprocess.run(['git', 'scan-repo'], 
                                         capture_output=True, 
                                         text=True)
                    os.chdir(current_dir)
                    
                    if result.returncode == 0:
                        # Return to main UI after scan completes
                        self.load_main_ui()
                    else:
                        raise Exception(result.stderr or "An error occurred during the scan")
                        
                except Exception as e:
                    os.chdir(current_dir)
                    self.show_message(
                        'Error',
                        f'Failed to scan repository:\n{str(e)}',
                        'error',
                        self.scan_repository  # Callback to return to repository selection
                    )

        def handle_back():
            self.load_main_ui()

        # Add new message handlers to CustomWebEnginePage
        original_message_handler = self.web_page.javaScriptConsoleMessage
        def new_message_handler(level, message, line, source):
            if message.startswith('action:'):
                action = message.split(':')[1]
                if action == 'browse':
                    handle_browse()
                elif action == 'start_scan':
                    handle_start_scan()
                elif action == 'back':
                    handle_back()
                elif action == 'message_ok':
                    if hasattr(self, '_message_callback') and self._message_callback:
                        self._message_callback()
                        self._message_callback = None
                else:
                    original_message_handler(level, message, line, source)
        
        self.web_page.javaScriptConsoleMessage = new_message_handler

    def show_scan_results(self, results):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Scan Results</title>
            <style>
                body {{
                    font-family: -apple-system, system-ui, sans-serif;
                    margin: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h2 {{
                    color: #07439C;
                    margin-bottom: 20px;
                }}
                .results-container {{
                    margin: 20px 0;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 4px;
                    overflow-x: auto;
                }}
                pre {{
                    margin: 0;
                    white-space: pre-wrap;
                    font-family: monospace;
                }}
                .back-btn {{
                    padding: 10px 20px;
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    margin-top: 20px;
                }}
                .back-btn:hover {{
                    background-color: #5a6268;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Scan Results</h2>
                <div class="results-container">
                    <pre>{results}</pre>
                </div>
                <button class="back-btn" onclick="console.log('action:back')">Back to Repository Selection</button>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(html_content)

if __name__ == '__main__':
    try:
        # Initialize QApplication first
        app = QApplication(sys.argv)
        
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
