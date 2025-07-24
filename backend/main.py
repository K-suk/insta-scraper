import uuid
import asyncio
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from loguru import logger

from scraper.fetch import scrape_job

app = FastAPI()

# CORS設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROGRESS: Dict[str, Dict] = {}


@app.post("/scrape")
async def start_scrape(data: Dict):
    usernames: List[str] = data.get("usernames", [])
    hashtags: List[str] = data.get("hashtags", [])
    max_items: int = data.get("max_items", 10)
    columns: List[str] = data.get("columns", [])

    job_id = uuid.uuid4().hex
    # async関数をバックグラウンドタスクとして実行
    asyncio.create_task(scrape_job(job_id, usernames, hashtags, max_items, columns, PROGRESS))
    PROGRESS[job_id] = {"progress": 0, "status": "queued"}
    logger.info("Created job {} with data: {}", job_id, data)
    return {"job_id": job_id}


@app.get("/progress/{job_id}")
async def get_progress(job_id: str):
    if job_id not in PROGRESS:
        logger.warning("Job {} not found in PROGRESS. Available jobs: {}", job_id, list(PROGRESS.keys()))
        raise HTTPException(status_code=404, detail="Job not found")
    progress_data = PROGRESS[job_id]
    logger.info("Progress for job {}: {}", job_id, progress_data)
    return progress_data


@app.get("/download/{job_id}")
async def download(job_id: str):
    info = PROGRESS.get(job_id)
    if not info or info.get("status") != "done":
        raise HTTPException(status_code=404, detail="Not ready")
    path = Path(info["path"])
    if not path.exists():
        logger.error("File not found: {}", path)
        raise HTTPException(status_code=404, detail="File missing")
    filename = f"instagram_reels_{path.stat().st_mtime_ns}.csv"
    return FileResponse(path, media_type="text/csv", filename=filename)
