"""JSON destination widget with confirmation for the final filename."""
from pathlib import Path

from processing.gui.wrappers import WidgetWrapper, InvalidParameterValue
from qgis.PyQt.QtWidgets import (
    QFileDialog, QHBoxLayout, QLineEdit, QMessageBox, QToolButton, QWidget,
)
from qgis.core import QgsVariantUtils

from .profile_paths import json_path


class ProfileDestinationWidgetWrapper(WidgetWrapper):
    def createWidget(self, **kwargs):
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit(panel)
        self.button = QToolButton(panel)
        self.button.setText("…")
        self.button.setToolTip("設定JSONの保存先を選択")
        layout.addWidget(self.edit)
        layout.addWidget(self.button)
        self._confirmed = None
        self.edit.textChanged.connect(self._changed)
        self.button.clicked.connect(self._browse)
        return panel

    def _changed(self):
        self._confirmed = None
        self.widgetValueHasChanged.emit(self)

    def _confirm(self, filename):
        if Path(filename).exists() and self._confirmed != filename:
            answer = QMessageBox.question(
                self.widget, "設定JSONの上書き確認",
                "次のファイルを上書きしますか？\n" + filename,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return False
        self._confirmed = filename
        return True

    def _browse(self):
        # Confirm only after appending the suffix, even on platforms whose
        # native save dialog does not supply an extension.
        filename, _ = QFileDialog.getSaveFileName(
            self.widget, "設定JSONの保存先", self.edit.text(), "JSON (*.json)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if filename:
            filename = json_path(filename)
            if self._confirm(filename):
                self.edit.setText(filename)
                self._confirmed = filename

    def setValue(self, value):
        self.edit.setText("" if QgsVariantUtils.isNull(value) else str(value))

    def value(self):
        filename = json_path(self.edit.text())
        if not filename:
            return None
        if not self._confirm(filename):
            raise InvalidParameterValue()
        return filename
