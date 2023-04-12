"""
Representations of tiles and parts of tiles.
"""

import dataclasses
from dataclasses import dataclass
from typing import Iterable, Sequence, Self

from surfigures.draw.ray_trace import IRayTrace, EmptyRayTrace


@dataclass(frozen=True)
class PositionedLabel:
    """
    Some text to draw using ImageMagick over a tile.
    """
    x: float
    """x position ratio"""
    y: float
    """y position ratio"""
    msg: str
    """label contents"""

    def at(self, row: int, col: int, tile_size_x: int, tile_size_y: int, spacing_x: int, spacing_y: int) -> Sequence[str]:
        """
        Produce an ``-annotate`` option which draws this label on a montage.
        """
        x = round((self.x + col) * tile_size_x + (2 * col + 1) * spacing_x)
        y = round((self.y + row) * tile_size_y + (2 * row + 1) * spacing_y)
        return (
            '-annotate',
            f'0x0+{x}+{y}',
            self.msg
        )


@dataclass(frozen=True)
class LazyTile:
    """
    Inputs which can create a tile.
    """

    ray_trace: IRayTrace
    labels: Iterable[PositionedLabel] = dataclasses.field(default_factory=tuple)

    def labels2args(self, row: int, col: int, tile_size_x: int, tile_size_y: int,
                    spacing_x: int, spacing_y: int) -> list[str]:
        """
        :returns: ``-annotate`` flags for all labels in this tile
        """
        annots = (label.at(row, col, tile_size_x, tile_size_y, spacing_x, spacing_y) for label in self.labels)
        return [arg for annot in annots for arg in annot]

    @classmethod
    def text_only(cls, text: str, x: float = 0.15, y: float = 0.20) -> Self:
        """
        Create a tile containing only a block of text (without brain images).
        """
        return cls(EmptyRayTrace(), [PositionedLabel(msg=text, x=x, y=y)])
