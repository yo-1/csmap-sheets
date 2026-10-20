"""Inspect the upload ZIP; unavailable scanners and scan errors fail."""
import argparse
import ast
import configparser
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
# Only installed scanners are invoked, without a shell.
import subprocess  # nosec B404
import sys
import tempfile
import zipfile


def check_archive(package):
    if package.stat().st_size > 25_000_000:
        raise ValueError("Package exceeds the default QGIS upload limit")
    with zipfile.ZipFile(package) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if not names or len(names) != len(set(names)):
            raise ValueError("Empty ZIP or duplicate paths")
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if (".." in entry.filename or "\\" in entry.filename
                    or path.is_absolute() or ":" in entry.filename
                    or path.parts[0] != "csmap_sheets"):
                raise ValueError("Invalid ZIP path: " + entry.filename)
            if any(part.startswith(".") or part in {
                "__pycache__", "__MACOSX", "tests"
            } for part in path.parts):
                raise ValueError("Unexpected path: " + entry.filename)
            mode = entry.external_attr >> 16
            if mode & 0o111 or stat.S_ISLNK(mode):
                raise ValueError("Executable or symlink: " + entry.filename)
            if path.suffix.lower() in {
                ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib",
                ".bat", ".sh", ".ps1", ".cmd",
            }:
                raise ValueError("Forbidden file type: " + entry.filename)
            if path.suffix == ".py":
                ast.parse(archive.read(entry).decode("utf-8"), entry.filename)
        for name in ("metadata.txt", "__init__.py", "LICENSE", "NOTICE"):
            if "csmap_sheets/" + name not in names:
                raise ValueError("Missing required file: " + name)
        metadata = configparser.ConfigParser()
        metadata.optionxform = str
        metadata.read_string(
            archive.read("csmap_sheets/metadata.txt").decode()
        )
        general = metadata["general"]
        required = (
            "name", "description", "version", "qgisMinimumVersion", "author",
            "email", "about", "tracker", "repository", "homepage", "icon",
        )
        for key in required:
            if not general.get(key, "").strip():
                raise ValueError("Missing metadata: " + key)
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", general["email"]):
            raise ValueError("Invalid email format")
        if "/" in general["author"]:
            raise ValueError("Invalid author")
        for key in ("experimental", "deprecated", "hasProcessingProvider"):
            if key in general and general[key].lower() not in {
                "true", "false", "yes", "no", "0", "1",
            }:
                raise ValueError("Invalid boolean: " + key)
        if "csmap_sheets/" + general["icon"] not in names:
            raise ValueError("Missing icon")
        versions = [
            general["qgisMinimumVersion"], general["qgisMaximumVersion"]
        ]
        parsed = [tuple(map(int, v.split("."))) for v in versions]
        if parsed[0] > parsed[1]:
            raise ValueError("Invalid QGIS version range")
        source = archive.read("csmap_sheets/engine/pipeline.py").decode()
        assignments = {
            n.targets[0].id: ast.literal_eval(n.value)
            for n in ast.parse(source).body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
            and isinstance(n.value, ast.Constant)
        }
        if assignments.get("VERSION") != general["version"]:
            raise ValueError("Metadata/banner version mismatch")
        if archive.testzip():
            raise ValueError("ZIP CRC failure")
        return {"files": len(names), "version": general["version"]}


def scan(package, output):
    output.mkdir(parents=True, exist_ok=True)
    archive_result = check_archive(package)
    with tempfile.TemporaryDirectory() as temp:
        with zipfile.ZipFile(package) as archive:
            archive.extractall(temp)
        commands = {
            "flake8": [sys.executable, "-m", "flake8", temp],
            "bandit": [sys.executable, "-m", "bandit", "-r", temp,
                       "-f", "json", "--quiet"],
            "secrets": [sys.executable, "-m", "detect_secrets", "scan",
                        "--all-files", temp],
        }
        for name, command in commands.items():
            # Fixed interpreter/modules; only the temporary path varies.
            result = subprocess.run(  # nosec B603
                command, capture_output=True, text=True,
                timeout=180, check=False, shell=False,
            )
            (output / (name + ".stdout")).write_text(result.stdout)
            (output / (name + ".stderr")).write_text(result.stderr)
            if result.returncode:
                raise ValueError(name + " failed; see " + str(output))
            if name == "bandit":
                report = json.loads(result.stdout)
                if report["results"] or report["errors"]:
                    raise ValueError("Bandit findings or scan errors")
            if name == "secrets" and json.loads(result.stdout)["results"]:
                raise ValueError("Potential secret detected")
    report = dict(archive_result, sha256=hashlib.sha256(
        package.read_bytes()).hexdigest(), passed=True)
    (output / "summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    scan(args.package, args.output)
