"""
Runs the study on YOUR machine.

  python run_all.py --verify    # ~15-30 min: 4 small instances x 7 methods x 20 runs, then compares with results_reference/
  python run_all.py --fresh     # full study (several hours); moves any existing results/ to results_backup_<time>/
  python run_all.py --resume    # continue an interrupted run (finished blocks are skipped)

IMPORTANT: the runner skips every (instance, method) block that is already in results/csv/runs.csv. If you copy someone
else's runs.csv into results/, NOTHING is recomputed. Use --fresh to be sure your own runs are produced.
"""
import subprocess, sys, os, shutil, time
here = os.path.dirname(os.path.abspath(__file__))
py = sys.executable
res = os.path.join(here, "results")
def run(*args):
    print(">>", *args, flush=True)
    subprocess.check_call([py, *args], cwd=here)
mode = sys.argv[1] if len(sys.argv) > 1 else ""
if mode not in ("--verify", "--fresh", "--resume"):
    print(__doc__); sys.exit(1)
runs_csv = os.path.join(res, "csv", "runs.csv")
if mode in ("--verify", "--fresh") and os.path.exists(runs_csv):
    backup = os.path.join(here, "results_backup_" + time.strftime("%Y%m%d_%H%M%S"))
    shutil.move(res, backup)
    print("existing results moved to", backup)
for d in ("csv", "conv", "tables", "figures"):
    os.makedirs(os.path.join(res, d), exist_ok=True)
run("src/collect_env.py")
if mode == "--verify":
    run("src/validate_port.py")
    run("src/run_experiments.py", "--group", "main", "--instances", "eil51", "berlin52", "st70", "kroA100")
    run("src/compare_with_reference.py")
    print("VERIFY DONE - send results/ (runs.csv, comparison_with_reference.txt, environment.txt, validation_log.txt)")
else:
    run("src/validate_port.py")
    run("src/run_experiments.py", "--group", "main")
    run("src/run_experiments.py", "--group", "ablation")
    run("src/run_experiments.py", "--group", "large", "--runs", "10")
    run("src/analyze.py")
    run("src/make_paper_data.py")
    run("src/compare_with_reference.py")
    print("ALL DONE - send the folder results/")
