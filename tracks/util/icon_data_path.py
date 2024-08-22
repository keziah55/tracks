from pathlib import Path
from qtpy.QtGui import QIcon, QPixmap, QColor
from qtpy.QtCore import Qt


def get_data_path():
    """Return Path to dir where Tracks data is stored"""
    p = Path.home().joinpath(".tracks")
    if not p.exists():
        p.mkdir(parents=True)
    return p


def get_icon_path(name, ext="svg") -> Path:
    """Return Path to icon [name].[ext]"""
    file = Path(__file__).parents[2].joinpath("images", "icons", f"{name}.{ext}")
    if file.exists():
        return file
    else:
        raise FileNotFoundError(f"Icon '{file}' not found.")


def get_icon(name, ext="svg") -> QIcon:
    """Return QIcon of [name].[ext]"""
    file = get_icon_path(name, ext=ext)
    return QIcon(str(file))


def make_foreground_icon(
    name, foregroundColour, ext="svg", returnType="icon"
) -> QIcon | QPixmap:
    """Open {name}.{ext} icon and change the colour to `foregroundColour`.

    Parameters
    ----------
    name : str
        Name of icon file (without extension)
    foregroundColour : str or QColor
        Colour to make the icon
    ext : str
        Icon file extension. Default is "svg"
    returnType : {"icon", "pixmap"}
        Whether to return a QIcon or a QPixmap. Default is "icon"
    """
    if returnType not in ["icon", "pixmap"]:
        raise ValueError(f"Invalid icon return type {returnType}")
    if isinstance(foregroundColour, str):
        foregroundColour = QColor(foregroundColour)
    file = get_icon_path(name, ext=ext)
    px0 = QPixmap(str(file))
    px1 = QPixmap(px0.size())
    px1.fill(foregroundColour)
    px1.setMask(px0.createMaskFromColor(Qt.transparent))
    if returnType == "icon":
        return QIcon(px1)
    else:
        return px1

