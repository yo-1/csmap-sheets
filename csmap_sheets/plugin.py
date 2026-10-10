"""QGIS GUI integration. Copyright (C) 2026 Yoichi Wada. GPL-3.0-only."""

from pathlib import Path
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QEvent, QObject, QTimer
from qgis.PyQt.QtWidgets import (
    QAction,
    QApplication,
    QAbstractSpinBox,
    QComboBox,
)
from qgis.core import QgsApplication
from .provider import CSMapProvider


class _WheelGuard(QObject):
    """Prevent accidental value changes while the long dialog is scrolled."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and isinstance(
            obj, (QAbstractSpinBox, QComboBox)
        ):
            return True
        return super().eventFilter(obj, event)


class CSMapSheetsPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.action = None
        self.wheel_guard = _WheelGuard()

    def initProcessing(self):
        if self.provider is None:
            self.provider = CSMapProvider()
            QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()
        self.action = QAction(
            QIcon(str(Path(__file__).with_name("icon.svg"))),
            "CS立体図・国土基本図図郭出力",
            self.iface.mainWindow(),
        )
        self.action.triggered.connect(self.open_dialog)
        self.iface.addPluginToRasterMenu("CS Map Sheets", self.action)
        self.iface.addToolBarIcon(self.action)

    def open_dialog(self):
        import processing

        def protect_controls():
            dialog = QApplication.activeModalWidget()
            if dialog is None:
                return
            widgets = dialog.findChildren(
                QAbstractSpinBox
            ) + dialog.findChildren(QComboBox)
            for widget in widgets:
                widget.installEventFilter(self.wheel_guard)
                widget.setToolTip(
                    (widget.toolTip() + "\n" if widget.toolTip() else "")
                    + "誤操作防止のためマウスホイールでは変更できません。クリックまたはキー入力で設定してください。"
                )

        QTimer.singleShot(0, protect_controls)
        processing.execAlgorithmDialog("csmapsheets:create")

    def unload(self):
        if self.action is not None:
            self.iface.removePluginRasterMenu("CS Map Sheets", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.deleteLater()
            self.action = None
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
