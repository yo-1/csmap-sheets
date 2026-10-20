"""QGIS sidecar style for transparent map-sheet indexes."""
from pathlib import Path

SHEET_INDEX_STYLE = '''<qgis version="3.44.0" styleCategories="Symbology">
  <renderer-v2 type="singleSymbol" symbollevels="0">
    <symbols>
      <symbol name="0" type="fill" alpha="1" clip_to_extent="1">
        <layer class="SimpleFill" enabled="1" pass="0">
          <Option type="Map">
            <Option name="style" type="QString" value="no"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_color" type="QString" value="60,60,60,255"/>
            <Option name="outline_width" type="QString" value="0.2"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="joinstyle" type="QString" value="miter"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
'''


def write_sheet_index_style(index_path):
    """QGIS automatically reads the same-basename QML on first layer load."""
    Path(index_path).with_suffix(".qml").write_text(
        SHEET_INDEX_STYLE, encoding="utf-8"
    )
