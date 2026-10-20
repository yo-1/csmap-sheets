"""Readers for Japanese forestry airborne-laser DEM deliverables. GPL-3.0-only.

Supported products are LEM+CSV(or .txt) metadata pairs, XYZ/CSV regular grids,
TIFF+world-file rasters, GeoTIFF rasters, and ZIP containers of those files.

LEMの対応メタデータファイルは、規則上は.csv拡張子だが実態として.txt拡張子で
提供される場合がある（2026-09-30 ユーザー報告）。判定は拡張子ではなく中身の
CSV構造（is_lem_metadata）で行うため、.csv/.txtいずれの拡張子でも認識できる。
同一stemに両方存在する場合は.csvを優先する。

注意：.txt拡張子は、上記のLEM対応メタデータとは無関係に、それ自体が標高値を
含む単体のXYZ/CSVグリッドファイルとしても使われる（検証用データでは「txt形式」等の
フォルダーに、.lem companionを持たない最大約100MB規模の.txtが大量に同居する
ケースが確認されている）。そのため is_lem_metadata() はファイル全体ではなく
先頭の固定バイト数（LEM_METADATA_PROBE_BYTES）のみを読んで判定する
「プローブ」方式にしている。v0.9.1では全文読み込みで判定していたため、この
種の大容量.txtが多数存在する検証用データでQGISが長時間「応答なし」になる回帰
バグを引き起こしていた（v0.9.2で修正、CHANGELOG.md参照）。
"""

import csv
import hashlib
import math
from pathlib import Path, PurePosixPath
import re
import zipfile

import numpy as np

NODATA = -999999.0
ARCHIVE_MEMBER_LIMIT = 512 * 1024 * 1024
ARCHIVE_TOTAL_LIMIT = 8 * 1024 * 1024 * 1024
SIDECARS = {".tfw", ".tifw", ".wld", ".prj", ".aux.xml"}
PRIMARY = {".lem", ".csv", ".txt", ".xyz", ".tif", ".tiff"}


def _decode(data):
    for encoding in ("utf-8-sig", "cp932", "shift_jis"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    raise ValueError("Text encoding is neither UTF-8 nor CP932/Shift_JIS")


def _key(value):
    return re.sub(r"[\s　_()（）・]+", "", value).lower()


# LEMメタデータ候補の判定(is_lem_metadata)に読み込むバイト数の上限。実測した本物の
# メタデータCSV(companion)は最大でも数十KB程度だったが、森林航空レーザ成果のデータには
# 同じ命名規則で最大約100MBに達する単体の.txtグリッドファイルが同居するフォルダー
# (「txt形式」等)が存在することが判明した(2026-09-30 ユーザー報告)。これらは.lem companion
# ではなく、それ自体が標高値を含む独立したテキストグリッドであり、メタデータ判定のために
# ファイル全体を読み込むと、大量の大容量ファイルに対してI/O・メモリ確保が積み重なり、
# QGISが長時間「応答なし」になる不具合が実際に発生した。そのため判定は先頭の一定バイト数
# だけを読む「プローブ」方式に変更する。実測の本物メタデータ(最大約35KB)に対して十分な
# 余裕(約7倍)を持たせた値。
LEM_METADATA_PROBE_BYTES = 262144  # 256 KiB


def _parse_metadata_fields(text, path):
    """Extract the aliased LEM header fields from already-decoded CSV text."""
    result = {}
    for row in csv.reader(text.splitlines()):
        if len(row) >= 2 and row[0].strip():
            result[_key(row[0])] = row[1].strip()
    aliases = {
        "nx": ("東西方向の点数", "東西方向点数"),
        "ny": ("南北方向の点数", "南北方向点数", "記録レコード数"),
        "dx": ("東西方向のデータ間隔", "東西方向データ間隔"),
        "dy": ("南北方向のデータ間隔", "南北方向データ間隔"),
        "south_n": ("区画左下x座標",),
        "west_e": ("区画左下y座標",),
        "north_n": ("区画右上x座標",),
        "east_e": ("区画右上y座標",),
        "zone": ("平面直角座標系番号",),
        "survey_year": ("測量年",),
        "sheet": ("図名",),
    }
    values = {}
    for name, names in aliases.items():
        value = next(
            (
                result.get(_key(n))
                for n in names
                if result.get(_key(n)) not in (None, "")
            ),
            None,
        )
        if value is not None:
            values[name] = value
    for required in (
        "nx",
        "ny",
        "dx",
        "dy",
        "south_n",
        "west_e",
        "north_n",
        "east_e",
    ):
        if required not in values:
            raise ValueError(
                f"LEM metadata CSV is missing: {required} ({path})"
            )
    for name in ("nx", "ny", "zone"):
        if name in values:
            values[name] = int(float(values[name]))
    for name in ("dx", "dy", "south_n", "west_e", "north_n", "east_e"):
        values[name] = float(values[name])
    return values


def read_lem_metadata(path):
    """Read the companion CSV header defined for LEM mesh elevation files.

    Reads the whole file. Call only on a file already confirmed (via
    is_lem_metadata()) to be a small metadata companion, not on an arbitrary
    candidate that might be a large text grid.
    """
    text, encoding = _decode(Path(path).read_bytes())
    values = _parse_metadata_fields(text, path)
    values["encoding"] = encoding
    return values


def _decode_head(path, max_bytes=LEM_METADATA_PROBE_BYTES):
    """Decode only the leading max_bytes of a file.

    Drops a possibly-truncated final line so a cut multi-byte sequence or an
    incomplete row doesn't corrupt decoding. Used to test LEM-metadata
    candidacy without reading an entire, potentially very large, file.
    """
    with open(path, "rb") as f:
        chunk = f.read(max_bytes)
    if len(chunk) == max_bytes:
        cut = chunk.rfind(b"\n")
        if cut > 0:
            chunk = chunk[:cut]
    return _decode(chunk)


def is_lem_metadata(path):
    """Cheaply test whether `path` looks like a LEM companion metadata file.

    Reads only a bounded leading chunk (LEM_METADATA_PROBE_BYTES), not the
    whole file -- see the module-level comment on that constant for why.
    仮定：本物のメタデータの必須フィールドは、このプローブ範囲内(先頭256KiB)に
    収まっている。この前提を超える巨大な本物メタデータが将来出てきた場合は、
    grid扱いに誤判定される(未確認の残存リスク)。
    """
    try:
        text, _ = _decode_head(path)
        metadata = _parse_metadata_fields(text, path)
        return metadata["nx"] > 0 and metadata["ny"] > 0
    except (OSError, UnicodeError, ValueError, csv.Error):
        return False


def _coordinate_scale(meta, requested="auto"):
    if requested != "auto":
        scale = float(requested)
        if scale <= 0 or not math.isfinite(scale):
            raise ValueError("Invalid LEM coordinate scale")
        return scale
    # Standard files normally store plane rectangular X/Y as centimetre
    # integers.
    # Select the scale whose stated bounds best match point count and spacing.
    target_n = meta["ny"] * meta["dy"]
    target_e = meta["nx"] * meta["dx"]
    candidates = (1.0, 0.01, 0.001)

    def error(scale):
        dn = abs((meta["north_n"] - meta["south_n"]) * scale - target_n) / max(
            target_n, 1e-9
        )
        de = abs((meta["east_e"] - meta["west_e"]) * scale - target_e) / max(
            target_e, 1e-9
        )
        return dn + de

    scale = min(candidates, key=error)
    if error(scale) > 0.05:
        raise ValueError(
            "LEM metadata bounds do not agree wi"
            "th point counts/spacing; set forest"
            "_lem_coordinate_scale"
        )
    return scale


def read_lem(
    path, metadata_path, max_pixels, coordinate_scale="auto", feedback=None
):
    """Return (array, geotransform, metadata) for a fixed-width LEM file."""
    meta = read_lem_metadata(metadata_path)
    nx, ny = meta["nx"], meta["ny"]
    if nx <= 0 or ny <= 0 or nx * ny > max_pixels:
        raise ValueError("LEM grid exceeds input pixel limit")
    scale = _coordinate_scale(meta, coordinate_scale)
    raw = Path(path).read_bytes()
    text, encoding = _decode(raw)
    lines = [line.rstrip("\r\n") for line in text.splitlines() if line.strip()]
    if len(lines) != ny:
        raise ValueError(
            f"LEM row count mismatch: expected {ny}, found {len(lines)}"
        )
    array = np.full((ny, nx), NODATA, dtype="float32")
    for row, line in enumerate(lines):
        if feedback is not None and row % 256 == 0 and feedback.isCanceled():
            raise RuntimeError("Cancelled during LEM conversion")
        if len(line) < 10 + nx * 5:
            raise ValueError(
                f"LEM row {row + 1} is shorter than the fixed-width definition"
            )
        record = line[6:10].strip()
        if record and record.lstrip("+-").isdigit() and int(record) != row + 1:
            raise ValueError(f"LEM record number mismatch at row {row + 1}")
        for col in range(nx):
            field = line[10 + col * 5: 15 + col * 5].strip()
            try:
                value = int(field)
            except ValueError as exc:
                raise ValueError(
                    f"LEM invalid elevation at row {row + 1}, column {col + 1}"
                ) from exc
            if value not in (-9999, -1111):
                array[row, col] = value * 0.1
    west = meta["west_e"] * scale
    north = meta["north_n"] * scale
    gt = (west, meta["dx"], 0.0, north, 0.0, -meta["dy"])
    detail = {
        **meta,
        "coordinate_scale": scale,
        "lem_encoding": encoding,
        "metadata_path": str(metadata_path),
        "nodata_codes": [-9999, -1111],
    }
    return array, gt, detail


def _safe_member(name):
    p = PurePosixPath(name.replace("\\", "/"))
    return bool(
        name
        and not p.is_absolute()
        and ".." not in p.parts
        and not re.match(r"^[A-Za-z]:", name)
    )


def extract_archive(path, destination):
    """Safely extract only supported DEM members and required sidecars."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    extracted = []
    total = 0
    with zipfile.ZipFile(path) as archive:
        for entry in sorted(
            archive.infolist(), key=lambda e: e.filename.lower()
        ):
            if entry.is_dir():
                continue
            if not _safe_member(entry.filename):
                raise ValueError("Unsafe ZIP member path: " + entry.filename)
            suffix = Path(entry.filename).suffix.lower()
            compound = Path(entry.filename).name.lower().endswith(".aux.xml")
            if suffix not in PRIMARY | SIDECARS and not compound:
                continue
            if entry.file_size > ARCHIVE_MEMBER_LIMIT:
                raise ValueError(
                    "ZIP member exceeds 512 MiB: " + entry.filename
                )
            total += entry.file_size
            if total > ARCHIVE_TOTAL_LIMIT:
                raise ValueError(
                    "Supported ZIP members exceed 8 GiB uncompressed"
                )
            target = destination.joinpath(*PurePosixPath(entry.filename).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source, target.open("wb") as sink:
                while True:
                    block = source.read(1024 * 1024)
                    if not block:
                        break
                    sink.write(block)
            extracted.append(target)
    if not extracted:
        raise ValueError("ZIP contains no supported forestry DEM files")
    return extracted


def expand_sources(paths, work):
    expanded = []
    archives = []
    # フォルダごとに.csv一覧を一度だけ列挙してキャッシュする。修正前は companion.exists() が
    # False（同名.csvが無い）の LEM ファイル1個ごとに parent.glob('*') でフォルダ全件を
    # 再走査しており、対応CSVを1つも持たない大量のLEM（本件のような数百～1000件規模）では
    # O(件数^2) のファイルシステム走査になり、QGIS本体が長時間応答なしになっていた
    # （2026-09-28 ユーザー報告: 794件のLEM単体・対応CSVなしでハング）。
    csv_index_cache = {}

    def csv_index(directory):
        if directory not in csv_index_cache:
            # glob('*.csv')はLinux等の大文字小文字を区別するファイルシステムでは
            # '.CSV'等を拾えない。修正前の実装（parent.glob('*')を毎回全件走査し
            # p.suffix.lower()=='.csv'で判定）と同じ「拡張子は大文字小文字を区別しない」
            # 挙動を、キャッシュ後も保つため、ここでも glob('*') 全件から suffix.lower() で絞り込む。
            #
            # 森林航空レーザ成果のデータでは、LEMの対応メタデータファイルの拡張子が
            # 規則上は.csvだが実態は.txtになっている場合が多い（2026-09-30 ユーザー報告）。
            # is_lem_metadata()は中身のCSV構造で判定するため拡張子非依存で対応できるが、
            # .txtは単体のXYZグリッド入力としても使われる拡張子のため、同一stemに
            # .csvと.txtが両方存在する場合は.csvを優先する（同一ループ内で.csv側を
            # 後勝ちで上書きすることで、glob('*')の列挙順に依存せず優先順位を保証する）。
            entries = {}
            for p in directory.glob("*"):
                suffix = p.suffix.lower()
                if suffix == ".txt":
                    entries.setdefault(p.stem.lower(), p)
                elif suffix == ".csv":
                    entries[p.stem.lower()] = p
            csv_index_cache[directory] = entries
        return csv_index_cache[directory]

    for ordinal, value in enumerate(paths, 1):
        path = Path(value)
        if path.suffix.lower() == ".zip":
            token = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[
                :10
            ]
            members = extract_archive(
                path, Path(work) / f"archive_{ordinal:06d}_{token}"
            )
            expanded.extend(members)
            archives.append({"path": str(path), "members": len(members)})
        else:
            expanded.append(path)
            if path.suffix.lower() == ".lem":
                companion = path.with_suffix(".csv")
                if not companion.exists():
                    companion = path.with_suffix(".txt")
                if not companion.exists():
                    companion = csv_index(path.parent).get(
                        path.stem.lower(), companion
                    )
                if companion.exists() and companion not in expanded:
                    expanded.append(companion)
    return expanded, archives


def classify_sources(paths):
    'Identify primary files and avoid tr' \
        'eating LEM metadata CSV/TXT as an X' \
        'YZ grid.'
    files = [Path(p) for p in paths]
    # companion候補は.csvと.txtの両方を対象にする（2026-09-30 ユーザー報告: 森林航空レーザ
    # 成果のデータでは対応メタデータの拡張子が.txtの場合が多い）。同一stemに両方存在する
    # 場合は.csvを優先する（expand_sources()のcsv_index()と同じ優先順位）。
    by_key = {}
    for p in files:
        suffix = p.suffix.lower()
        if suffix == ".txt":
            by_key.setdefault((p.parent, p.stem.lower()), p)
        elif suffix == ".csv":
            by_key[(p.parent, p.stem.lower())] = p
    result = []
    for p in files:
        suffix = p.suffix.lower()
        if suffix in SIDECARS or p.name.lower().endswith(".aux.xml"):
            continue
        if suffix == ".lem":
            header = by_key.get((p.parent, p.stem.lower()))
            if header is None or not is_lem_metadata(header):
                raise ValueError(
                    "LEM requires its companion metadata"
                    " CSV/TXT (same stem, .csv or .txt) "
                    "with LEM header fields: " + str(p)
                )
            result.append({"kind": "lem", "path": p, "metadata": header})
        elif suffix in (".csv", ".txt") and is_lem_metadata(p):
            if not any(
                q.suffix.lower() == ".lem"
                and q.parent == p.parent
                and q.stem.lower() == p.stem.lower()
                for q in files
            ):
                raise ValueError(
                    "LEM metadata file (.csv/.txt) has n"
                    "o companion .lem file: " + str(p)
                )
        elif suffix in (".csv", ".txt", ".xyz"):
            result.append({"kind": "grid", "path": p})
        elif suffix in (".tif", ".tiff"):
            result.append({"kind": "raster", "path": p})
    if not result:
        raise ValueError("No primary forestry DEM files were detected")
    return result


def autodetect_xyz(path, axis_order="north_east"):
    "Detect delimiter/header/columns for a conventional three-column XYZ grid."
    text, encoding = _decode(Path(path).read_bytes())
    lines = [line for line in text.splitlines() if line.strip()]
    for skip, line in enumerate(lines[:100]):
        delimiter = (
            "comma"
            if "," in line
            else "tab"
            if "\t" in line
            else "semicolon"
            if ";" in line
            else "space"
        )
        row = (
            line.split()
            if delimiter == "space"
            else next(
                csv.reader(
                    [line],
                    delimiter={"comma": ",", "tab": "\t", "semicolon": ";"}[
                        delimiter
                    ],
                )
            )
        )
        numeric = []
        for index, value in enumerate(row):
            try:
                float(value)
                numeric.append(index + 1)
            except ValueError:
                pass
        if len(numeric) >= 3:
            return dict(
                text_encoding=encoding,
                text_delimiter=delimiter,
                text_skip_rows=skip,
                text_columns=numeric[:3],
                text_axis_order=axis_order,
            )
    raise ValueError(
        "Could not detect three numeric XYZ columns: " + str(path)
    )
