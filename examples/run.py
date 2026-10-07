"""Choose a checkpoint and a live Bugsmith decision example from two menus."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.common import main

if __name__ == "__main__":
    main()
