import os
import sys

# Add the backend directory to the Python search path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import and expose the FastAPI app
from app.main import app
