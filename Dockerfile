FROM python:3.12-slim

WORKDIR /app

# Install dependencies before copying source so Docker layer-caches them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy source
COPY . .

# Flask backend default; overridden in docker-compose for the Streamlit service
EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
