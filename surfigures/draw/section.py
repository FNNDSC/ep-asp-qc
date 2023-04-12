from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from surfigures.draw.ray_trace import HemiRayTrace, WholeBrainRayTrace, HemiPos, WholeBrainPos
from surfigures.draw.tile import PositionedLabel, LazyTile
from surfigures.draw import constants

LABEL_LR = [
    PositionedLabel(x=constants.HEMI_LABEL_RATIO_L, y=constants.HEMI_LABEL_RATIO_Y, msg='L'),
    PositionedLabel(x=constants.HEMI_LABEL_RATIO_R, y=constants.HEMI_LABEL_RATIO_Y, msg='R'),
]

LABEL_RL = [
    PositionedLabel(x=constants.HEMI_LABEL_RATIO_L, y=constants.HEMI_LABEL_RATIO_Y, msg='R'),
    PositionedLabel(x=constants.HEMI_LABEL_RATIO_R, y=constants.HEMI_LABEL_RATIO_Y, msg='L'),
]

RowPair = tuple[
    LazyTile, LazyTile, LazyTile, LazyTile, LazyTile, LazyTile,
    LazyTile, LazyTile, LazyTile, LazyTile, LazyTile, LazyTile
]
"""
Two rows of tiles, each row having 6 columns.
"""


@dataclass(frozen=True)
class Section:
    # maybe it'd be cool to also show the T1/T2 like `verify_image`
    surface_left: Path
    surface_right: Path
    textblock_left: str
    textblock_right: str

    def to_row_pair(self) -> RowPair:
        """
        Create two rows depicting left and right hemispheres, as well as whole brain figures.
        """
        return (
            self._whole_brain(WholeBrainPos.top, labels=LABEL_LR),
            self._whole_brain(WholeBrainPos.bottom, labels=LABEL_RL),
            self._hemi_left(HemiPos.default),
            self._hemi_left(HemiPos.left),
            self._hemi_left(HemiPos.right),
            LazyTile.text_only(self.textblock_left),

            self._whole_brain(WholeBrainPos.front, labels=LABEL_RL),
            self._whole_brain(WholeBrainPos.back, labels=LABEL_LR),
            self._hemi_right(HemiPos.flipped),
            self._hemi_right(HemiPos.left),
            self._hemi_right(HemiPos.right),
            LazyTile.text_only(self.textblock_right),
        )

    def _hemi_left(self, position: HemiPos) -> LazyTile:
        return LazyTile(HemiRayTrace(self.surface_left, position))

    def _hemi_right(self, position: HemiPos) -> LazyTile:
        return LazyTile(HemiRayTrace(self.surface_right, position))

    def _whole_brain(self, position: WholeBrainPos, labels: Iterable[PositionedLabel]) -> LazyTile:
        rt = WholeBrainRayTrace(self.surface_left, self.surface_right, position)
        return LazyTile(rt, labels)
