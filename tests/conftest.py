"""pytest configuration"""
import sys
from pathlib import Path

# Add satcore to path
sys.path.insert(0, str(Path(__file__).parent.parent))
