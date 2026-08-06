FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./requirements.txt
# Install CPU-only torch first: the default PyPI wheel bundles CUDA runtime
# libraries (multi-GB, high memory footprint) that aren't needed here and
# can OOM small production instances during audio similarity scoring.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

EXPOSE 8000

# Keep the image default production-safe; local auto-reload should be opt-in.
CMD ["sh", "-c", "python -m app.core.init_db && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]