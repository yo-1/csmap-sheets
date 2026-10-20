"""Check Markdown repository links without network access."""
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/yo-1/csmap-sheets/"
LINK = re.compile(r'!?\[[^\]\n]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')


def check(paths, root=ROOT):
    checked = 0
    errors = []
    for path in paths:
        content = path.read_text(encoding="utf-8")
        content = re.sub(r"```.*?```", "", content, flags=re.S)
        for match in LINK.finditer(content):
            target = match.group(1).strip("<>")
            url = urlsplit(target)
            if target.startswith(REPOSITORY + "blob/main/"):
                relative = target[len(REPOSITORY + "blob/main/"):]
                destination = root / unquote(urlsplit(relative).path)
            elif url.scheme or url.netloc:
                if url.scheme not in {"https", "http", "mailto"}:
                    errors.append(f"{path}: unexpected URL: {target}")
                continue
            else:
                destination = path.parent / unquote(url.path) if (
                    url.path
                ) else path
            checked += 1
            if not destination.exists():
                errors.append(f"{path}: missing target: {target}")
                continue
            if url.fragment and destination.suffix == ".md":
                headings = re.findall(
                    r"^#{1,6} +(.+?) *#* *$",
                    destination.read_text(encoding="utf-8"), re.M,
                )
                anchors = set()
                counts = {}
                for heading in headings:
                    slug = re.sub(r"[^\w\- ]", "", heading.lower())
                    slug = slug.replace(" ", "-")
                    count = counts.get(slug, 0)
                    anchors.add(f"{slug}-{count}" if count else slug)
                    counts[slug] = count + 1
                if unquote(url.fragment) not in anchors:
                    errors.append(f"{path}: missing anchor: {target}")
    if errors:
        raise ValueError("\n".join(errors))
    return checked


if __name__ == "__main__":
    paths = [p for p in sorted(ROOT.rglob("*.md")) if ".git" not in p.parts]
    print(f"Validated {check(paths)} repository links in {len(paths)} files")
