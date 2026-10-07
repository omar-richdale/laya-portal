"""Review proposed repair actions against the objective; never execute them."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.common import main

if __name__ == "__main__":
    main("alignment")
