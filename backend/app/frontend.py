"""Serve the React build from the same web server as the API."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def add_frontend_routes(app: FastAPI, directory: Path) -> None:
    index_file = directory / "index.html"
    if not index_file.is_file():
        # Backend development still works before the frontend has been built.
        return

    # Vite puts JavaScript/CSS in assets and the country outlines in maps.
    for folder_name in ("assets", "maps"):
        folder = directory / folder_name
        if folder.is_dir():
            app.mount(
                f"/{folder_name}", StaticFiles(directory=folder), name=folder_name
            )

    @app.get("/favicon.svg", include_in_schema=False)
    def favicon():
        return FileResponse(directory / "favicon.svg")

    # Return the React entry page for saved links and browser refreshes.
    @app.get("/", include_in_schema=False)
    @app.get("/countries", include_in_schema=False)
    @app.get("/countries/{iso3}", include_in_schema=False)
    @app.get("/compare", include_in_schema=False)
    @app.get("/reports", include_in_schema=False)
    @app.get("/explorer", include_in_schema=False)
    def frontend_page():
        return FileResponse(index_file, headers={"Cache-Control": "no-cache"})
