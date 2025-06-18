import os

host = os.getenv("HOST", "0.0.0.0")  # noqa: S104
port = os.getenv("PORT", "8088")
bind = f"{host}:{port}"

workers = int(os.getenv("WORKERS", "1"))

worker_class = "uvicorn.workers.UvicornWorker"

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
