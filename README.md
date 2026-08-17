# High-Throughput Social Media Data Ingestion & Influencer Discovery Pipeline

**Project Type:** Production Technical Assessment / Data Engineering Challenge  
**Target Domain:** Tourism Industry Influencer Analytics (`zelflive` integration)

## Overview
This repository contains a high-performance, asynchronous data mining and influencer identification pipeline built to extract, process, and analyze social media posts and creator profiles at scale. Designed to bypass strict rate-limiting and dynamic DOM structures, the system identifies high-value creators meeting strict engagement thresholds (100k+ followers, 1M+ likes).

## Core Architecture & Technical Implementation
1. **Zero-DOM API Interception (`new_scraper.py`):** 
   - Bypasses traditional HTML parsing by hooking directly into internal search JSON streams (`search/general/full/`), ensuring complete immunity to frontend layout changes.
2. **Asynchronous Worker Concurrency (`scraper.py`):** 
   - Implements `asyncio.Semaphore` rate-limiting to execute concurrent profile extractions safely across thousands of data points without triggering IP blocks.
3. **Automated Engagement & Verification (`engagement.py`):** 
   - Features automated interaction scripts coupled with a verification loop to confirm comment deployment and post-state tracking.
4. **Persistent Data Storage (`db.py`):** 
   - Dynamic schema generation and parameterized execution mapping directly to a PostgreSQL/SQLite backend sink.

## Tech Stack
* **Language:** Python 3.10+
* **Async & Scraping:** Playwright (Async), DrissionPage, BeautifulSoup4
* **Data & Storage:** PostgreSQL (`psycopg2`), Pandas, SQLite
* **Utilities:** `playwright_stealth`, JSON/CSV serialization

---
*Developed as a robust, production-ready response to a complex enterprise data extraction specification.*
