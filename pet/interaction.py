from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtGui import QImage, QPixmap


def opaque_at(pixmap: QPixmap, point: QPoint, threshold: int = 24) -> bool:
    """Alpha-mask hit test; transparent sprite padding stays click-through logically."""
    if pixmap.isNull() or not pixmap.rect().contains(point):
        return False
    image: QImage = pixmap.toImage()
    return image.pixelColor(point).alpha() >= threshold
