
import os
import sys

# Set environment variable to force native UI
os.environ['GENIE_USE_NATIVE_UI'] = 'true'

# Override imports to prevent QtWebEngineCore from being imported
class ImportBlocker:
    def find_module(self, fullname, path=None):
        if fullname == 'PySide6.QtWebEngineCore':
            return self
        return None
        
    def load_module(self, fullname):
        raise ImportError(f"The {fullname} module is not available in this build")

# Install the import blocker
import sys
sys.meta_path.insert(0, ImportBlocker())
