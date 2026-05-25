FROM python:3.12-slim

WORKDIR /app

# System deps (none needed — resvg-py has a pre-built wheel)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer-cached)
COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[web]"

# Copy source
COPY . .
RUN pip install --no-cache-dir -e ".[web]"

EXPOSE 8000

CMD ["uvicorn", "signforge.web:app", "--host", "0.0.0.0", "--port", "8000"]
