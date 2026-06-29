import threading

# Shared state between Web Server and Scheduler threads
status = "idle"  # idle, syncing, success, failed
last_sync_time = "尚未运行"
next_sync_time = "尚未计算"
error_message = ""
total_docs_synced = 0

# Thread event to wake up the scheduler immediately for manual syncs
sync_event = threading.Event()
