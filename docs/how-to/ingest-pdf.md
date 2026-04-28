# How to Ingest a PDF

There are three ways to ingest a PDF into your Second Brain:

## 1. Drag and Drop via the Web UI
1. Start the application by running `python -m brain.app`.
2. Open your browser to `http://localhost:8000/upload`.
3. Drag and drop your PDF file into the designated drop zone, or click the zone to browse your file system.
4. The system will upload the file and trigger the ingestion pipeline in the background.

## 2. Using the OS Background Watchdog
1. Ensure the application is running (`python -m brain.app`).
2. Open your file explorer (Finder/Windows Explorer).
3. Move or download a `.pdf` file directly into the `raw/` directory in the project folder.
4. The background Watchdog will automatically detect the file and trigger the ingestion pipeline. Check your terminal logs for progress!

## 3. Via the Command Line
If you want to manually run the pipeline or ingest all unprocessed files in the `raw/` folder, use the ingest script:

**Ingest a specific file:**
```bash
python -m brain.ingest /path/to/your/document.pdf
```

**Ingest all unprocessed files in `raw/`:**
```bash
python -m brain.ingest --all
```
