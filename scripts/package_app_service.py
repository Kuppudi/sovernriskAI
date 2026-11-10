"""Create a source ZIP for Azure App Service. Run after building the frontend."""

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# An explicit list keeps credentials, local data, and node_modules out of the ZIP.
APP_FOLDERS = ("backend/app", "backend/alembic", "ingestion", "frontend/dist")
APP_FILES = (
    "backend/__init__.py",
    "requirements.txt",
    "requirements.lock",
    "pyproject.toml",
    "alembic.ini",
    "startup.sh",
)


def create_package(project: Path, output: Path) -> None:
    for folder in APP_FOLDERS:
        if output.resolve().is_relative_to((project / folder).resolve()):
            raise ValueError(
                "Put the ZIP outside the application folders, for example dist/app-service.zip."
            )
    required = ("frontend/dist/index.html", "frontend/dist/maps/world-countries.json")
    for name in (*APP_FILES, *required):
        if not (project / name).is_file():
            raise ValueError(
                f"Required file missing: {name}. Build the frontend first."
            )

    files = [project / name for name in APP_FILES]
    for folder in APP_FOLDERS:
        directory = project / folder
        if not directory.is_dir():
            raise ValueError(f"Required folder missing: {folder}")
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(project)
            if "__pycache__" in relative.parts or any(
                part.startswith(".") for part in relative.parts
            ):
                continue
            if path.suffix in (".pyc", ".pyo"):
                continue
            files.append(path)

    if not any(path.parent.name == "assets" and path.suffix == ".js" for path in files):
        raise ValueError("Frontend JavaScript missing. Run npm run build first.")

    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(project.resolve()):
            raise ValueError(
                f"Deployment files must stay inside the project: {path.relative_to(project)}"
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=path.relative_to(project).as_posix())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "dist" / "app-service.zip"
    )
    args = parser.parse_args()
    try:
        create_package(PROJECT_ROOT, args.output)
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    print(f"App Service package: {args.output}")


if __name__ == "__main__":
    main()
