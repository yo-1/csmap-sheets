"""QGIS plugin entry point. Copyright (C) 2026 Yoichi Wada. GPL-3.0-only."""

def classFactory(iface):
    from .plugin import CSMapSheetsPlugin
    return CSMapSheetsPlugin(iface)
