"""Writes results/environment.txt (hardware and library versions) - send it with your results."""
import os, platform, sys
import numpy, scipy, pandas, matplotlib, numba
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lines = [f"python {platform.python_version()}", f"numpy {numpy.__version__}", f"scipy {scipy.__version__}",
         f"pandas {pandas.__version__}", f"matplotlib {matplotlib.__version__}", f"numba {numba.__version__}",
         f"os {platform.platform()}", f"machine {platform.machine()}", f"processor {platform.processor()}",
         f"cpu_count {os.cpu_count()}"]
os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
open(os.path.join(ROOT, "results", "environment.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
