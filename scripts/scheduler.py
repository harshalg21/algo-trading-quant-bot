import os
import time
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Fix OpenBLAS Windows Memory Allocation Error
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def run_afternoon_job():
    print(f"\n[CRON SCHEDULER]: Triggering 3:15 PM IST Trade Scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    python_exe = sys.executable
    script_path = Path(__file__).parent / "automated_daily_job.py"
    try:
        subprocess.run([python_exe, str(script_path)], capture_output=False)
        print("[CRON SCHEDULER]: 3:15 PM Trade Scan Job Finished Successfully.")
    except Exception as e:
        print(f"[CRON SCHEDULER]: Error running 3:15 PM job: {e}")

def run_night_eod_job():
    print(f"\n[CRON SCHEDULER]: Triggering 11:30 PM IST Night EOD Summary at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    python_exe = sys.executable
    script_path = Path(__file__).parent.parent / "src" / "database" / "journal.py"
    try:
        subprocess.run([python_exe, str(script_path)], capture_output=False)
        print("[CRON SCHEDULER]: 11:30 PM Night EOD Job Finished Successfully.")
    except Exception as e:
        print(f"[CRON SCHEDULER]: Error running 11:30 PM Night EOD job: {e}")

def main():
    print("="*75)
    print(" ⏰ BULLETPROOF DUAL CRON SCHEDULER STARTED")
    print(" • 3:15 PM IST  : Daily Trade Scan (Equity + Commodity)")
    print(" • 11:30 PM IST : Final Night EOD Portfolio & Journal Summary")
    print("="*75 + "\n")

    last_afternoon_date = None
    last_night_date = None

    while True:
        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        weekday = now.weekday()  # 0=Monday, 4=Friday
        
        curr_hour = now.hour
        curr_min = now.minute

        if weekday < 5:
            # 1. Check 3:15 PM Afternoon Scan Trigger (15:15 to 23:29)
            if (curr_hour == 15 and curr_min >= 15) or (15 < curr_hour < 23):
                if last_afternoon_date != today_date:
                    last_afternoon_date = today_date
                    run_afternoon_job()

            # 2. Check 11:30 PM Night EOD Trigger (23:30 to 23:59)
            if curr_hour == 23 and curr_min >= 30:
                if last_night_date != today_date:
                    last_night_date = today_date
                    run_night_eod_job()

        time.sleep(15)

if __name__ == "__main__":
    main()
