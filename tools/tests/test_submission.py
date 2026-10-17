"""Ensure malformed packages and scanner failures cannot receive a pass."""
import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile
from tools.check_plugin_package import build
from tools.check_submission import check_archive, scan


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / "valid.zip"
        with contextlib.redirect_stdout(io.StringIO()):
            build(self.package)

    def test_valid_distribution(self):
        self.assertGreater(check_archive(self.package)["files"], 20)

    def test_reject_invalid_packages(self):
        with zipfile.ZipFile(self.package) as source:
            entries = [(i, source.read(i)) for i in source.infolist()]
        for case in ("traversal", "license", "executable", "bytecode",
                     "version", "boolean", "syntax", "duplicate"):
            with self.subTest(case=case):
                target = self.root / (case + ".zip")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    with zipfile.ZipFile(target, "w") as dest:
                        for info, data in entries:
                            if case == "license" and info.filename.endswith(
                                "/LICENSE"
                            ):
                                continue
                            if case == "version" and info.filename.endswith(
                                "/metadata.txt"
                            ):
                                data = data.replace(b"version=", b"version=9")
                            if case == "boolean" and info.filename.endswith(
                                "/metadata.txt"
                            ):
                                data = data.replace(
                                    b"experimental=True", b"experimental=oops"
                                )
                            if case == "syntax" and info.filename.endswith(
                                "/algorithm.py"
                            ):
                                data = b"def broken(\n"
                            dest.writestr(info, data)
                        if case == "traversal":
                            dest.writestr("../escape", "bad")
                        if case == "executable":
                            entry = zipfile.ZipInfo("csmap_sheets/extra.py")
                            entry.external_attr = 0o100755 << 16
                            dest.writestr(entry, "pass\n")
                        if case == "bytecode":
                            dest.writestr("csmap_sheets/extra.pyc", b"bad")
                        if case == "duplicate":
                            dest.writestr(entries[0][0], entries[0][1])
                with self.assertRaises((ValueError, SyntaxError)):
                    check_archive(target)

    def test_scanner_failure_is_not_a_pass(self):
        failure = subprocess.CompletedProcess([], 2, "", "tool failed")
        with patch(
            "tools.check_submission.subprocess.run", return_value=failure
        ):
            with self.assertRaisesRegex(ValueError, "flake8 failed"):
                scan(self.package, self.root / "report")
