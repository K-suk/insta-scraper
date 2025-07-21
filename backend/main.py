import uuid
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from scraper.fetch import scrape_job

app = FastAPI()

PROGRESS: Dict[str, Dict] = {}


@app.post("/scrape")
async def start_scrape(data: Dict, background: BackgroundTasks):
    usernames: List[str] = data.get("usernames", [])
    hashtags: List[str] = data.get("hashtags", [])
    max_items: int = data.get("max_items", 10)
    columns: List[str] = data.get("columns", [])

    job_id = uuid.uuid4().hex
    background.add_task(scrape_job, job_id, usernames, hashtags, max_items, columns, PROGRESS)
    PROGRESS[job_id] = {"progress": 0, "status": "queued"}
    return {"job_id": job_id}


@app.get("/progress/{job_id}")
async def get_progress(job_id: str):
    if job_id not in PROGRESS:
        raise HTTPException(status_code=404, detail="Job not found")
    return PROGRESS[job_id]


@app.get("/download/{job_id}")
async def download(job_id: str):
    info = PROGRESS.get(job_id)
    if not info or info.get("status") != "done":
        raise HTTPException(status_code=404, detail="Not ready")
    path = Path(info["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing")
    filename = f"instagram_reels_{path.stat().st_mtime_ns}.csv"
    return FileResponse(path, media_type="text/csv", filename=filename)
