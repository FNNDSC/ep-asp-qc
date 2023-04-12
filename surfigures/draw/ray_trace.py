"""
Pre-configurations of MNI ``ray_trace`` for creating figures of brain surfaces.
"""

import abc
import enum
import os
from dataclasses import dataclass
from typing import Sequence, Iterable


class IRayTrace(abc.ABC):
    """
    ``ray_trace`` inputs and pre-configuration.
    """

    def to_cmd(self, bg: str, x_size: int, y_size: int, output: str | os.PathLike) -> Sequence[str]:
        """
        Produce a command which runs ``ray_trace`` with this as input.
        """
        return (
            'ray_trace', '-shadows', '-output', str(output),
            '-bg', bg, '-crop', '-size', str(x_size), str(y_size),
            *self.to_args()
        )

    @abc.abstractmethod
    def to_args(self) -> Iterable[str]:
        """
        Produce arguments for ``ray_trace`` which specify this as input.
        """
        ...


class EmptyRayTrace(IRayTrace):
    """
    Empty image file ``ray_trace`` configuration.
    """

    def to_args(self) -> Iterable[str]:
        return []


class HemiPos(tuple[str, ...], enum.Enum):
    """
    ``ray_trace`` view orientations suitable for a single brain hemisphere.
    """
    default = ('-view', '0.77', '-0.18', '-0.6', '0.55', '0.6', '0.55')
    flipped = ('-view', '-0.77', '-0.18', '-0.6', '-0.55', '0.6', '0.55')
    left = ('-left',)
    right = ('-right',)


class WholeBrainPos(str, enum.Enum):
    """
    ``ray_trace`` view orientations suitable for left and right hemispheres together.
    """
    top = '-top'
    bottom = '-bottom'
    front = '-front'
    back = '-back'


@dataclass(frozen=True)
class HemiRayTrace(IRayTrace):
    surface: os.PathLike
    view: HemiPos

    def to_args(self) -> Iterable[str]:
        return *self.view.value, self.surface


@dataclass(frozen=True)
class WholeBrainRayTrace(IRayTrace):
    surface_left: os.PathLike
    surface_right: os.PathLike
    view: WholeBrainPos

    def to_args(self) -> Iterable[str]:
        return self.view.value, self.surface_left, self.surface_right
