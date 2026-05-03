"""Run timesfm_pce_forecast.ipynb cells sequentially in a single Python process.

Used to surface errors cell by cell so they can be fixed.
- getpass is patched to use the FRED API key from the notebook prompt text.
- Plots are saved instead of shown (matplotlib Agg backend).
"""

import io
import json
import os
import sys
import traceback
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

NB_PATH = Path("G:/Coding/For Work/BUOD/Brent_simulation/TimesFM/timesfm_pce_forecast.ipynb")
FRED_KEY = "4840f2b6d06620ecc858b373a4669c43"

# Patch getpass to return the FRED key non-interactively.
import getpass as _getpass
_getpass.getpass = lambda prompt="": FRED_KEY

# Stub display() so non-Jupyter exec doesn't NameError.
def display(*args, **kwargs):
    for a in args:
        print(a)

shared_ns = {
    "__name__": "__main__",
    "display": display,
    "get_ipython": lambda: None,
}

nb = json.loads(NB_PATH.read_text(encoding="utf-8"))

START_CELL = int(os.environ.get("START_CELL", "0"))
END_CELL = int(os.environ.get("END_CELL", str(len(nb["cells"]))))

for idx, cell in enumerate(nb["cells"]):
    if cell["cell_type"] != "code":
        continue
    if idx < START_CELL or idx >= END_CELL:
        continue
    src = "".join(cell["source"])
    print(f"\n{'='*70}\n[CELL {idx} | id={cell['id']}]\n{'='*70}")
    print(src)
    print(f"{'-'*70}")
    try:
        exec(compile(src, f"<cell {idx}>", "exec"), shared_ns)
        print(f"[CELL {idx}] OK")
    except Exception:
        print(f"[CELL {idx}] FAILED:")
        traceback.print_exc()
        sys.exit(1)

print("\nAll cells in range completed.")
