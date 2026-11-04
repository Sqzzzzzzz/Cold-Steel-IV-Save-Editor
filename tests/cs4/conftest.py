import sys
import os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
os.environ.setdefault('QT_QPA_PLATFORM','windows' if os.name=='nt' else 'offscreen')
