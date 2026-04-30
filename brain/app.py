import os
import subprocess
import sys
import uvicorn
import time
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from brain.server import app, RAW_DIR, brain_graph, brain_index
from brain.ingest import ingest_document
from brain.parser import MARKITDOWN_EXTENSIONS

WATCHED_EXTENSIONS = {'.pdf'} | MARKITDOWN_EXTENSIONS

class DocumentHandler(FileSystemEventHandler):
    def on_created(self, event):
        ext = os.path.splitext(event.src_path)[1].lower()
        if not event.is_directory and ext in WATCHED_EXTENSIONS:
            print(f"[Watchdog] New file detected: {event.src_path}")
            try:
                # Small delay to ensure file is fully written before reading
                time.sleep(2)
                ingest_document(event.src_path, brain_graph, brain_index)
            except Exception as e:
                print(f"[Watchdog] Failed to auto-ingest {event.src_path}: {e}")

def start_watchdog():
    """Start the file watcher in a background thread."""
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)
        
    event_handler = DocumentHandler()
    observer = Observer()
    observer.schedule(event_handler, path=RAW_DIR, recursive=False)
    observer.start()

    print(f"[*] Watchdog started. Monitoring {RAW_DIR} for new files...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def _ensure_frontend_built():
    """Build the React frontend if dist/index.html is missing."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    dist_index = os.path.join(base_dir, "frontend", "dist", "index.html")
    frontend_dir = os.path.join(base_dir, "frontend")

    if os.path.exists(dist_index):
        return

    if not os.path.isdir(frontend_dir):
        print("[*] No frontend/ directory found — skipping build.")
        return

    print("[*] frontend/dist not found — building React app (first run)...")
    node_modules = os.path.join(frontend_dir, "node_modules")
    if not os.path.isdir(node_modules):
        print("[*] Installing npm dependencies...")
        result = subprocess.run(
            ["npm", "install"],
            cwd=frontend_dir,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        if result.returncode != 0:
            print("[!] npm install failed — frontend will not be available.")
            return

    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    if result.returncode != 0:
        print("[!] npm run build failed — frontend will not be available.")
    else:
        print("[*] Frontend built successfully.")


def main():
    """Main entry point for the Second Brain application."""
    print("================================")
    print(" SECOND BRAIN INITIALIZING...   ")
    print("================================")

    _ensure_frontend_built()
    
    # Start watchdog in a separate thread
    watcher_thread = Thread(target=start_watchdog, daemon=True)
    watcher_thread.start()
    
    # Start FastAPI server
    print("[*] Starting Web UI on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
