"""Test the upload ZIP with QGIS, including the real Processing dialog."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock
import zipfile
from qgis.core import QgsApplication, Qgis
from qgis.PyQt.QtCore import QObject, QUrl, Qt, pyqtSlot
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtWidgets import (
    QApplication, QDialogButtonBox, QTextBrowser, QWidget,
)
from tools.check_submission import check_archive


class UrlCapture(QObject):
    def __init__(self):
        super().__init__()
        self.urls = []

    @pyqtSlot(QUrl)
    def capture(self, url):
        self.urls.append(url.toString())


def check_help(dialog, screenshots):
    """Click real help anchors and the standard button without a browser."""
    capture = UrlCapture()
    QDesktopServices.setUrlHandler("https", capture, "capture")
    try:
        dialog.resize(1400, 1000)
        dialog.show()
        QApplication.processEvents()
        browser = dialog.findChild(QTextBrowser, "textShortHelp")
        if browser is None or not browser.isVisible():
            raise ValueError("Processing help pane is not visible")
        base = "https://github.com/yo-1/csmap-sheets/blob/main/docs/"
        for label, filename in (
            ("利用手順書", "user-guide.md"),
            ("推奨設定", "recommended-settings.md"),
        ):
            cursor = browser.document().find(label)
            if cursor.isNull():
                raise ValueError("Help label missing: " + label)
            cursor.setPosition(cursor.selectionStart() + 1)
            browser.setTextCursor(cursor)
            browser.ensureCursorVisible()
            point = browser.cursorRect(cursor).center()
            if browser.anchorAt(point) != base + filename:
                raise ValueError("Help link is not clickable: " + label)
            QTest.mouseClick(
                browser.viewport(), Qt.MouseButton.LeftButton, pos=point,
            )
            QApplication.processEvents()
            if capture.urls[-1:] != [base + filename]:
                raise ValueError("Help link did not open externally: " + label)
        boxes = dialog.findChildren(QDialogButtonBox)
        buttons = [
            box.button(QDialogButtonBox.StandardButton.Help) for box in boxes
            if box.button(QDialogButtonBox.StandardButton.Help) is not None
        ]
        if len(buttons) != 1 or not buttons[0].isVisible():
            raise ValueError("Expected one standard Help button")
        QTest.mouseClick(buttons[0], Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        if capture.urls != [
            base + "user-guide.md", base + "recommended-settings.md",
            base + "user-guide.md",
        ]:
            raise ValueError("Unexpected browser destinations")
        if screenshots:
            screenshots.mkdir(parents=True, exist_ok=True)
            browser.verticalScrollBar().setValue(0)
            for name, width, height in (
                ("dialog-wide.png", 1400, 1000),
                ("dialog-narrow.png", 1000, 850),
            ):
                dialog.resize(width, height)
                QApplication.processEvents()
                if not dialog.grab().save(str(screenshots / name)):
                    raise ValueError("Could not save screenshot: " + name)
        print(json.dumps({"help_links": capture.urls}, ensure_ascii=False))
    finally:
        QDesktopServices.unsetUrlHandler("https")


def check(package, screenshots=None):
    check_archive(package)
    app = QgsApplication([], False)
    app.initQgis()
    from processing.core.Processing import Processing
    from processing.tools import general

    Processing.initialize()
    with tempfile.TemporaryDirectory() as temp:
        with zipfile.ZipFile(package) as archive:
            archive.extractall(temp)
        sys.path.insert(0, temp)
        import csmap_sheets

        if not Path(csmap_sheets.__file__).is_relative_to(temp):
            raise ValueError("Imported source tree instead of the upload ZIP")
        iface = Mock()
        window = QWidget()
        iface.mainWindow.return_value = window
        plugin = csmap_sheets.classFactory(iface)
        plugin.initGui()
        if plugin.action.icon().isNull():
            raise ValueError("Plugin icon could not be loaded")
        plugin.initProcessing()
        if not QgsApplication.processingRegistry().algorithmById(
            "csmapsheets:create"
        ):
            raise ValueError("Processing algorithm was not registered")
        # Standalone tests have no desktop iface; supply only the GUI parent.
        general.iface = iface
        dialog = general.createAlgorithmDialog("csmapsheets:create")
        check_help(dialog, screenshots)
        wrapper = dialog.mainWidget().wrappers["SAVE_PROFILE"]
        wrapper.setValue(str(Path(temp) / "settings"))
        if wrapper.value() != str(Path(temp) / "settings.json"):
            raise ValueError("Destination wrapper did not append .json")
        dialog.close()
        plugin.unload()
        if QgsApplication.processingRegistry().providerById("csmapsheets"):
            raise ValueError("Processing provider was not removed")
        iface.removeToolBarIcon.assert_called_once()
        print("QGIS", Qgis.QGIS_VERSION)
        print(json.dumps({"import": True, "init_gui": True, "dialog": True,
                          "profile_wrapper": True, "unload": True}))
    # Keep the application alive until SIP wrappers are destroyed on exit.
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--screenshots", type=Path)
    args = parser.parse_args()
    application = check(args.package, args.screenshots)
