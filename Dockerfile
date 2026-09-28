FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home buddy && mkdir -p /app/data && chown -R buddy:buddy /app
USER buddy
ENV PYTHONUNBUFFERED=1 BUDDY_DB_PATH=/app/data/buddy.db
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3)"
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8765"]
