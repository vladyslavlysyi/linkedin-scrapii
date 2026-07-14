FROM python:3.11-slim-bookworm

WORKDIR /app



COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browser binaries
RUN playwright install --with-deps chromium

COPY . .

CMD ["python", "-m", "scraper.main"]
