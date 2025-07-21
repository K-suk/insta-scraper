import random
import time
from pathlib import Path
from typing import Dict, List

import pandas as pd
from loguru import logger
from playwright.sync_api import sync_playwright

from .login import load_context, WAIT_SEC
from .csv_utils import build_dataframe


def scrape_job(job_id: str, usernames: List[str], hashtags: List[str], max_items: int, columns: List[str], progress: Dict[str, Dict]):
    """Simulate scraping job."""
    logger.info("Starting scrape job {}", job_id)
    progress[job_id] = {"progress": 0, "status": "running"}

    results = []
    total_tasks = len(usernames) + len(hashtags)
    count = 0

    with sync_playwright() as p:
        browser, context = load_context(p)
        page = context.new_page()
        for user in usernames:
            logger.info("Scraping user {}", user)
            time.sleep(random.uniform(WAIT_SEC, WAIT_SEC * 2))
            results.append({
                "url": f"https://instagram.com/reel/{user}",
                "title": user,
                "caption": f"Sample caption for {user}",
                "posted_at": int(time.time())
            })
            count += 1
            progress[job_id]["progress"] = int(100 * count / total_tasks)

        for tag in hashtags:
            logger.info("Scraping hashtag {}", tag)
            time.sleep(random.uniform(WAIT_SEC, WAIT_SEC * 2))
            results.append({
                "url": f"https://instagram.com/reel/{tag}",
                "title": tag,
                "caption": f"Sample caption for #{tag}",
                "posted_at": int(time.time())
            })
            count += 1
            progress[job_id]["progress"] = int(100 * count / total_tasks)

        browser.close()

    df = build_dataframe(results, columns)
    out_dir = Path("backend/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{job_id}.csv"
    df.to_csv(csv_path, index=False)
    progress[job_id].update({"status": "done", "path": str(csv_path)})
    logger.info("Job {} complete", job_id)
