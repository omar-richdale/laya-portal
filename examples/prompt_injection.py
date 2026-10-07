"""Screen untrusted QA evidence and tool output before building an agent prompt."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.common import main

if __name__ == "__main__":
    main("injection")
