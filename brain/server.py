import os
import shutil
import markdown
import nh3
from fastapi import FastAPI, Request, File, UploadFile, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from brain.graph import BrainGraph
from brain.index import BrainIndex
from brain.search import BrainSearch
from brain.query import QueryEngine
from brain.ingest import ingest_pdf

app = FastAPI(title="Second Brain Terminal")

# Setup directories
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
RAW_DIR = os.path.join(BASE_DIR, "raw")
DOCS_DIR = os.path.join(BASE_DIR, "store", "documents")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# Mount static and templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize core engines
brain_graph = BrainGraph()
brain_index = BrainIndex()
brain_search = BrainSearch(brain_index, brain_graph)
query_engine = QueryEngine(brain_search)

class QueryRequest(BaseModel):
    query: str

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """Search/Q&A terminal prompt page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query")
async def handle_query(req: QueryRequest):
    """Accepts question, returns answer + sources (JSON)."""
    answer, sources = query_engine.query(req.query)
    return JSONResponse(content={"answer": answer, "sources": sources})

@app.get("/graph", response_class=HTMLResponse)
async def graph_page(request: Request):
    """Cytoscape.js knowledge graph page."""
    return templates.TemplateResponse("graph.html", {"request": request})

@app.get("/graph/data")
async def graph_data():
    """Graph nodes + edges as JSON for Cytoscape."""
    # Ensure graph is up to date
    brain_graph._load_from_files()
    return HTMLResponse(content=brain_graph.export_json(), media_type="application/json")

_NH3_TAGS = {
    "a", "b", "blockquote", "br", "code", "del", "div", "em", "h1", "h2",
    "h3", "h4", "h5", "h6", "hr", "i", "img", "li", "ol", "p", "pre",
    "s", "span", "strong", "table", "tbody", "td", "th", "thead", "tr", "ul",
}
_NH3_ATTRS = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title"},
    "*": {"class"},
}

def _safe_slug_path(base_dir: str, slug: str):
    """Return the resolved path for slug inside base_dir, or None if it escapes."""
    safe_name = os.path.basename(slug)
    candidate = os.path.realpath(os.path.join(base_dir, f"{safe_name}.md"))
    if candidate.startswith(os.path.realpath(base_dir) + os.sep):
        return candidate
    return None

@app.get("/doc/{slug}", response_class=HTMLResponse)
async def view_document(request: Request, slug: str):
    """Rendered Markdown document viewer."""
    doc_path = _safe_slug_path(DOCS_DIR, slug)

    if doc_path is None or not os.path.exists(doc_path):
        return HTMLResponse(content="Document not found", status_code=404)

    with open(doc_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    raw_html = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
    html_content = nh3.clean(raw_html, tags=_NH3_TAGS, attributes=_NH3_ATTRS)

    return templates.TemplateResponse("doc.html", {
        "request": request,
        "slug": slug,
        "content": html_content
    })

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Drag-and-drop PDF upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Save PDF to raw/, trigger ingest in background, return status."""
    safe_name = os.path.basename(file.filename or "")
    if not safe_name.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"message": "Only PDFs are allowed."})

    candidate = os.path.realpath(os.path.join(RAW_DIR, safe_name))
    if not candidate.startswith(os.path.realpath(RAW_DIR) + os.sep):
        return JSONResponse(status_code=400, content={"message": "Invalid filename."})

    file_path = candidate
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Trigger ingest in background
    background_tasks.add_task(ingest_pdf, file_path, brain_graph, brain_index)
    
    return {"filename": file.filename, "status": "Ingestion started in background"}
