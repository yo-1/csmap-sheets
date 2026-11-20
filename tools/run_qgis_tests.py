"""Standalone QGIS Python test runner (QT_QPA_PLATFORM=offscreen for CI).

Do not execute/import this script inside a running QGIS Desktop session or
through QGIS Dev Probe. It owns a separate QgsApplication lifecycle.
"""
import sys
import unittest
from qgis.core import QgsApplication

app = QgsApplication([], False)
app.initQgis()
from processing.core.Processing import Processing  # noqa: E402

Processing.initialize()
suite = unittest.defaultTestLoader.discover(
    "csmap_sheets/tests", top_level_dir="."
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
# Keep app alive until all SIP wrappers have been destroyed at process exit.
sys.exit(not result.wasSuccessful())
