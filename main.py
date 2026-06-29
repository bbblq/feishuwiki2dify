import os
import time

# Load env variables from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sync_to_dify import sync

def main():
    run_once = os.environ.get("RUN_ONCE", "false").lower() in ("true", "1", "yes")
    
    if run_once:
        print("RUN_ONCE is enabled. Executing sync once and exiting...")
        try:
            sync()
        except Exception as e:
            print(f"Error during execution: {e}")
            exit(1)
        print("Execution finished successfully.")
        return

    # Scheduling loop
    try:
        interval_minutes = float(os.environ.get("SYNC_INTERVAL_MINUTES", "60"))
    except ValueError:
        print("Invalid SYNC_INTERVAL_MINUTES. Defaulting to 60 minutes.")
        interval_minutes = 60.0

    print(f"Starting Feishu Wiki to Dify sync scheduler...")
    print(f"Sync Interval: {interval_minutes} minutes.")

    while True:
        print(f"\n--- Sync Run Started at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        try:
            sync()
        except Exception as e:
            print(f"Error occurred during sync: {e}")
        
        print(f"--- Sync Run Completed. Waiting for {interval_minutes} minutes before next run... ---")
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    main()
