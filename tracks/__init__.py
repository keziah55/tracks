from pathlib import Path
from qtpy.QtGui import QIcon, QPixmap, QColor
from qtpy.QtCore import Qt

def getIconPath(name, ext="svg") -> Path:
    """ Return Path to icon [name].[ext] """
    file = Path(__file__).parents[1].joinpath("images", "icons", f"{name}.{ext}")
    if file.exists():
        return file
    else:
        raise FileNotFoundError(f"Icon '{file}' not found.")

def getIcon(name, ext="svg") -> QIcon:
    """ Return QIcon of [name].[ext] """
    file = getIconPath(name, ext=ext)
    return QIcon(str(file))
        
def makeForegroundIcon(name, foregroundColour, ext="svg", returnType="icon") -> QIcon | QPixmap:
    """ Open {name}.{ext} icon and change the colour to `foregroundColour`.
    
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
    if returnType not in ['icon', 'pixmap']:
        raise ValueError(f"Invalid icon return type {returnType}")
    if isinstance(foregroundColour, str):
        foregroundColour = QColor(foregroundColour)
    file = getIconPath(name, ext=ext)
    px0 = QPixmap(str(file))
    px1 = QPixmap(px0.size())
    px1.fill(foregroundColour)
    px1.setMask(px0.createMaskFromColor(Qt.transparent))
    if returnType == 'icon':
        return QIcon(px1)
    else:
        return px1
        
__all__ = ["getIcon", "makeForegroundIcon"]