"""Build and validate a submission ZIP without tests or local data."""
import configparser
from pathlib import Path
import sys
import zipfile
from urllib.parse import urlparse


def build(destination):
    root = Path(__file__).resolve().parents[1]
    plugin = root / "csmap_sheets"
    metadata = configparser.ConfigParser(interpolation=None)
    metadata.read(plugin / "metadata.txt", encoding="utf-8")
    general = metadata["general"]
    required = ("name", "description", "about", "version", "author", "email",
                "qgisMinimumVersion", "homepage", "repository", "tracker")
    for key in required:
        if not general.get(key, "").strip():
            raise ValueError("Missing metadata: " + key)
    if "@" not in general["email"]:
        raise ValueError("Invalid contact email")
    for key in ("homepage", "repository", "tracker"):
        url = urlparse(general[key])
        if url.scheme != "https" or not url.netloc:
            raise ValueError("Invalid URL: " + key)
    for name in ("__init__.py", "metadata.txt", general["icon"]):
        if not (plugin / name).is_file():
            raise ValueError("Missing plugin file: " + name)
    allowed = {".py", ".txt", ".md", ".svg", ".json", ".csv", ".yml"}
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(plugin.rglob("*")):
            relative = path.relative_to(plugin)
            if not path.is_file() or path.is_symlink():
                continue
            if {"tests", "__pycache__"}.intersection(relative.parts):
                continue
            if (path.suffix not in allowed
                    and path.name not in {"LICENSE", "NOTICE"}):
                raise ValueError("Unexpected distribution file: " + str(path))
            info = zipfile.ZipInfo("csmap_sheets/" + relative.as_posix())
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity failed")
        print("Validated", len(archive.infolist()), "files:", destination)


if __name__ == "__main__":
    build(sys.argv[1])
