import os
import shutil
import markdown
import nh3
from fastapi import FastAPI, Request, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from brain.graph import BrainGraph
from brain.index import BrainIndex
from brain.search import BrainSearch
from brain.query import QueryEngine
from brain.ingest import ingest_document, INGEST_LOG
from brain.parser import MARKITDOWN_EXTENSIONS
from brain import llm

UPLOAD_EXTENSIONS = {'.pdf'} | MARKITDOWN_EXTENSIONS

app = FastAPI(title="Second Brain Terminal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/query")
async def handle_query(req: QueryRequest):
    """Accepts question, returns answer + sources (JSON)."""
    answer, sources = query_engine.query(req.query)
    return JSONResponse(content={"answer": answer, "sources": sources})

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

@app.get("/doc/{slug}")
async def view_document(request: Request, slug: str):
    """Rendered Markdown document viewer — HTML or JSON depending on Accept header."""
    doc_path = _safe_slug_path(DOCS_DIR, slug)

    if doc_path is None or not os.path.exists(doc_path):
        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse(status_code=404, content={"error": "Not found"})
        return HTMLResponse(content="Document not found", status_code=404)

    with open(doc_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    raw_html = markdown.markdown(md_text, extensions=["fenced_code", "tables"])
    content_html = nh3.clean(raw_html, tags=_NH3_TAGS, attributes=_NH3_ATTRS)

    if "application/json" in request.headers.get("accept", ""):
        # Parse YAML frontmatter manually to avoid test mocking issues
        title = slug.replace("_", " ").title()
        tags: list = []
        body = md_text
        if md_text.startswith("---"):
            end = md_text.find("---", 3)
            if end != -1:
                fm_block = md_text[3:end]
                for line in fm_block.splitlines():
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip('"\'')
                    elif line.startswith("tags:"):
                        raw = line.split(":", 1)[1].strip()
                        if raw.startswith("["):
                            tags = [t.strip().strip('"\'') for t in raw.strip("[]").split(",") if t.strip()]
                body = md_text[end + 3:].lstrip()
        else:
            # Try to get title from first H1
            for line in md_text.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
        return JSONResponse({
            "slug": slug,
            "title": title,
            "tags": tags,
            "content_html": content_html,
        })

    return templates.TemplateResponse(
        request, "doc.html", {"slug": slug, "content": content_html}
    )

@app.post("/settings")
async def save_settings(request: Request):
    """Persist LLM configuration to store/config.json."""
    form = await request.form()
    try:
        config = {
            "ollama_base_url": str(form.get("ollama_base_url", llm.DEFAULT_CONFIG["ollama_base_url"])).strip(),
            "tagger": {
                "backend": str(form.get("tagger_backend", "anthropic")),
                "ollama_model": str(form.get("tagger_ollama_model", llm.DEFAULT_CONFIG["tagger"]["ollama_model"])).strip(),
                "anthropic_model": str(form.get("tagger_anthropic_model", llm.DEFAULT_CONFIG["tagger"]["anthropic_model"])).strip(),
                "temperature": float(form.get("tagger_temperature", llm.DEFAULT_CONFIG["tagger"]["temperature"])),
            },
            "linker": {
                "backend": str(form.get("linker_backend", "anthropic")),
                "ollama_model": str(form.get("linker_ollama_model", llm.DEFAULT_CONFIG["linker"]["ollama_model"])).strip(),
                "anthropic_model": str(form.get("linker_anthropic_model", llm.DEFAULT_CONFIG["linker"]["anthropic_model"])).strip(),
                "temperature": float(form.get("linker_temperature", llm.DEFAULT_CONFIG["linker"]["temperature"])),
            },
        }
        llm.save_config(config)
        return JSONResponse({"status": "saved"})
    except (ValueError, TypeError) as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid value: {e}"})


@app.post("/settings/test-localai")
async def test_ollama_connection(request: Request):
    """Ping Ollama and return available model names."""
    data = await request.json()
    base_url = str(data.get("base_url", "http://localhost:11434")).strip()
    try:
        models = llm.list_ollama_models(base_url)
        return JSONResponse({"ok": True, "models": models})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


@app.get("/ingest/log")
async def ingest_log():
    """Return recent ingestion events including any LLM fallback warnings."""
    return JSONResponse(list(INGEST_LOG))


@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Save uploaded file to raw/, trigger ingest in background, return status."""
    safe_name = os.path.basename(file.filename or "")
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in UPLOAD_EXTENSIONS:
        return JSONResponse(status_code=400, content={"message": f"Unsupported file type: {ext or '(none)'}"})

    candidate = os.path.realpath(os.path.join(RAW_DIR, safe_name))
    if not candidate.startswith(os.path.realpath(RAW_DIR) + os.sep):
        return JSONResponse(status_code=400, content={"message": "Invalid filename."})

    file_path = candidate

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Trigger ingest in background
    background_tasks.add_task(ingest_document, file_path, brain_graph, brain_index)

    return {"filename": file.filename, "status": "Ingestion started in background"}


FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

if os.path.isdir(os.path.join(FRONTEND_DIST, "assets")):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")),
        name="frontend-assets",
    )


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    """Serve React SPA index.html for any non-API path in production."""
    index = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index):
        with open(index, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="Frontend not built. Run: cd frontend && npm run build",
        status_code=503,
    )
