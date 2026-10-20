"""Test the upload ZIP with QGIS, including the real Processing dialog."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock
import zipfile
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QWidget
from tools.check_submission import check_archive


def check(package):
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
        wrapper = dialog.mainWidget().wrappers["SAVE_PROFILE"]
        wrapper.setValue(str(Path(temp) / "settings"))
        if wrapper.value() != str(Path(temp) / "settings.json"):
            raise ValueError("Destination wrapper did not append .json")
        dialog.close()
        plugin.unload()
        if QgsApplication.processingRegistry().providerById("csmapsheets"):
            raise ValueError("Processing provider was not removed")
        iface.removeToolBarIcon.assert_called_once()
        print(json.dumps({"import": True, "init_gui": True, "dialog": True,
                          "profile_wrapper": True, "unload": True}))
    # Keep the application alive until SIP wrappers are destroyed on exit.
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    application = check(args.package)
