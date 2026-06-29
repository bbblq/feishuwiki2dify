import os
import time
import threading
from app import app
import state
from sync_to_dify import sync, load_settings

# Load env variables from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def start_web_server():
    print("Starting Web Dashboard on http://0.0.0.0:8080...")
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
        state.last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S")

def main():
    # Start web server thread
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()

    # Wait a moment for the server to bind and output startup logs
    time.sleep(1)

    print("Feishu Wiki to Dify sync scheduler initialized.")

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
        state.next_sync_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(next_time_epoch))
        
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
            
        print(f"Starting sync run at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
        run_sync_task()
        print("Sync run completed.")

if __name__ == "__main__":
    main()
