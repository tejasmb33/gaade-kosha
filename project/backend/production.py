"""Serve the built frontend and existing API from one origin.

Only frontend/dist is public. Data, models, source files and configuration are
never mounted. Uses the same backend, database and models as local development.
"""
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from .app import app


def mount_frontend(application, directory):
    directory=Path(directory).resolve()
    if not (directory/'index.html').is_file():
        raise RuntimeError('Frontend build missing. Run npm run build --prefix frontend.')
    application.mount('/', StaticFiles(directory=str(directory),html=True),name='frontend')
    return application


mount_frontend(app,Path(__file__).resolve().parents[1]/'frontend'/'dist')
