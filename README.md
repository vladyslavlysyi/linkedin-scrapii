# LinkedIn Job Scraper

A robust LinkedIn job scraper built with Python 3.11+, Playwright, and PostgreSQL. It runs inside Docker containers, supporting stealth mode and proxy rotation for scraping job listings while avoiding detection.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- Make sure ports `5432` are available on your system.

## Setup Instructions

1. **Configure Environment Variables**
   Rename the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and adjust the search parameters (`SEARCH_KEYWORDS`, `SEARCH_LOCATION`) and configure your proxies if you have them.

2. **Build and Run the Containers**
   In the project root directory (`linkedin_scraper/`), run:
   ```bash
   docker compose up --build -d
   ```
   This will spin up four services:
   - `db`: The PostgreSQL 15 database instance.
   - `scraper`: The Python Playwright scraper that fetches LinkedIn jobs in the background.
   - `api`: FastAPI backend that serves the scraped jobs.
   - `nginx`: Web server hosting the simple frontend UI on port 80.

3. **View the Web UI**
   Open your browser and navigate to `http://localhost` to view the gathered jobs.

4. **Check Logs**
   To see the scraper navigating LinkedIn, check the logs of the `scraper` service:
   ```bash
   docker compose logs -f scraper
   ```

## Database Schema

The scraper saves jobs into the `jobs` table in the `linkedin_jobs` database with the following fields:
- `id`: Serial Primary Key
- `title`: Job Title
- `company`: Company Name
- `location`: Job Location
- `date_posted`: Post Date
- `job_link`: URL to the job (Unique)
- `description`: Full HTML/Text job description
- `scraped_at`: Timestamp of the scrape

If a job is scraped again, the `UNIQUE` constraint on `job_link` triggers an upsert (`ON CONFLICT DO UPDATE`), refreshing the job's details without creating duplicates.

## Anti-bot measures implemented
- Random human-like delays (`3` to `9` seconds).
- `fake-useragent` dynamically randomizing the user-agent.
- Playwright's headless browser with bypassed webdriver flags.
- Proxy rotation setup included via environment variables.
