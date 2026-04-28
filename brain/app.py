import os
import uvicorn
import time
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from brain.server import app, RAW_DIR, brain_graph, brain_index
from brain.ingest import ingest_pdf

class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.pdf'):
            print(f"[Watchdog] New PDF detected: {event.src_path}")
            try:
                # Add a small delay to ensure file is fully written before reading
                time.sleep(2)
                ingest_pdf(event.src_path, brain_graph, brain_index)
            except Exception as e:
                print(f"[Watchdog] Failed to auto-ingest {event.src_path}: {e}")

def start_watchdog():
    """Start the file watcher in a background thread."""
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)
        
    event_handler = PDFHandler()
    observer = Observer()
    observer.schedule(event_handler, path=RAW_DIR, recursive=False)
    observer.start()
    
    print(f"[*] Watchdog started. Monitoring {RAW_DIR} for new PDFs...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def main():
    """Main entry point for the Second Brain application."""
    print("================================")
    print(" SECOND BRAIN INITIALIZING...   ")
    print("================================")
    
    # Start watchdog in a separate thread
    watcher_thread = Thread(target=start_watchdog, daemon=True)
    watcher_thread.start()
    
    # Start FastAPI server
    print("[*] Starting Web UI on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
