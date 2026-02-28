import sys
import os

# Ensure the root directory is in the path so we can import from 'src'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app
