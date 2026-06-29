import os
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from app import app
import state
from sync_to_dify import sync, load_settings

# Load env variables from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Force Python's logging module to format all logs (including Flask/Werkzeug) in Beijing Time (UTC+8)
def beijing_converter(*args):
    timestamp = args[0] if args else time.time()
    tz_beijing = timezone(timedelta(hours=8))
    dt = datetime.fromtimestamp(timestamp, tz_beijing)
    return dt.timetuple()

logging.Formatter.converter = beijing_converter

# Helper functions to get Beijing Time strings
def get_beijing_time_str():
    tz_beijing = timezone(timedelta(hours=8))
    return datetime.now(tz_beijing).strftime("%Y-%m-%d %H:%M:%S")

def get_beijing_time_str_from_epoch(epoch):
    tz_beijing = timezone(timedelta(hours=8))
    return datetime.fromtimestamp(epoch, tz_beijing).strftime("%Y-%m-%d %H:%M:%S")

def start_web_server():
    print(f"Starting Web Dashboard on http://0.0.0.0:8080... (Beijing Time: {get_beijing_time_str()})")
    # debug=False is required when running Flask in a background thread to prevent reloader conflicts
    app.run(host="0.0.0.0", port=8080, debug=False)

def run_sync_task():
    try:
        state.status = "syncing"
        state.error_message = ""
        
        # Trigger the sync logic
        sync()
        
        state.status = "success"
    except Exception as e:
        print(f"Error during sync: {e}")
        state.status = "failed"
        state.error_message = str(e)
    finally:
        state.last_sync_time = get_beijing_time_str()

def main():
    # Start web server thread
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()

    # Wait a moment for the server to bind and output startup logs
    time.sleep(1)

    print(f"Feishu Wiki to Dify sync scheduler initialized. (Beijing Time: {get_beijing_time_str()})")

    # Set event initially to run the first sync immediately on startup
    state.sync_event.set()

    while True:
        # Load current configuration settings dynamically
        settings = load_settings()
        
        # Check run once setting
        run_once_val = settings.get("RUN_ONCE", "false").lower() in ("true", "1", "yes")
        
        if run_once_val:
            print("RUN_ONCE is enabled. Executing sync once and exiting...")
            run_sync_task()
            # Wait a brief moment for stdout logs to write to file
            time.sleep(2)
            print("Execution finished. Exiting container.")
            return

        # Regular scheduling logic
        try:
            interval_minutes = float(settings.get("SYNC_INTERVAL_MINUTES", "60"))
        except ValueError:
            interval_minutes = 60.0

        interval_seconds = interval_minutes * 60.0
        next_time_epoch = time.time() + interval_seconds
        state.next_sync_time = get_beijing_time_str_from_epoch(next_time_epoch)
        
        print(f"\n[Scheduler] Next scheduled sync at: {state.next_sync_time} (Interval: {interval_minutes} minutes)")
        
        # Wait on event or timeout
        # If manual sync is requested, sync_event will be set and this returns True immediately
        triggered = state.sync_event.wait(timeout=interval_seconds)
        
        # Reset the event flag
        state.sync_event.clear()
        
        if triggered:
            print("\n[Scheduler] Sync triggered manually or initially on startup!")
        else:
            print("\n[Scheduler] Scheduled sync interval reached.")
            
        print(f"Starting sync run at {get_beijing_time_str()}...")
        run_sync_task()
        print("Sync run completed.")

if __name__ == "__main__":
    main()
