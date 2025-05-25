import os
from glob import glob

def get_latest_run_dir(logs_dir="logs"):
    if not os.path.exists(logs_dir):
        raise FileNotFoundError(f"Logs directory '{logs_dir}' does not exist.")
    run_dirs = [d for d in glob(os.path.join(logs_dir, '*')) if os.path.isdir(d)]
    if not run_dirs:
        raise FileNotFoundError("No run directories found in logs/.")
    # Sort by directory name (timestamp format)
    latest_run = sorted(run_dirs)[-1]
    return latest_run

def create_delta_folder():
    latest_run = get_latest_run_dir()
    delta_dir = os.path.join(latest_run, 'Delta')
    os.makedirs(delta_dir, exist_ok=True)
    print(f"Created Delta folder at: {delta_dir}")

if __name__ == "__main__":
    create_delta_folder() 