import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import os

WATCH_DIR = r"C:\Users\vyshn\Statistics"
DEBOUNCE_SECONDS = 5
COMMIT_MESSAGE = "auto-sync: updates"

ignore_paths = {".git", ".ipynb_checkpoints"}

class DebouncedHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.timer = None
        self.lock = threading.Lock()

    def on_any_event(self, event):
        for p in ignore_paths:
            if p in event.src_path:
                return
        with self.lock:
            if self.timer:
                self.timer.cancel()
            self.timer = threading.Timer(DEBOUNCE_SECONDS, self.do_commit)
            self.timer.start()

    def do_commit(self):
        try:
            subprocess.run(["git", "add", "."], cwd=WATCH_DIR, check=True)
            res = subprocess.run(["git", "status", "--porcelain"], cwd=WATCH_DIR, capture_output=True, text=True)
            if res.stdout.strip():
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                msg = f"{COMMIT_MESSAGE} @ {timestamp}"
                subprocess.run(["git", "commit", "-m", msg], cwd=WATCH_DIR, check=True)
                subprocess.run(["git", "push", "origin", "main"], cwd=WATCH_DIR, check=True)
                print(f"✅ Pushed at {timestamp}")
            else:
                print("No changes to commit.")
        except subprocess.CalledProcessError as e:
            print("⚠️ Git error:", e)

if __name__ == "__main__":
    os.chdir(WATCH_DIR)
    event_handler = DebouncedHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=True)
    observer.start()
    print("🕒 Auto-sync is running — watching:", WATCH_DIR)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
