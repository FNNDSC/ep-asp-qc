"""
Helper functions for preparing surfaces for figure generation.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from surfigures.draw.section import Section
from surfigures.util.runnable import Runnable, Runner


@dataclass(frozen=True)
class BaseHemiPreparer(Runnable[tuple[Path, str]]):
    """
    No-op surface file wrapper. Subclasses of ``DrawableHemiBuilder`` apply preprocessing
    to the surface to prepare the file for use with ``ray_trace``.
    """
    surface: Path

    def preprocess_surface_cmd(self, output: Path) -> Optional[Sequence[str | os.PathLike]]:
        return None

    def generate_textblock_cmd(self) -> Optional[Sequence[str | os.PathLike]]:
        return None

    def get_uniqueish_name(self) -> str:
        return self.surface.name

    def run(self, sp: Runner) -> tuple[Path, str]:
        tmp_colored = sp.tmp_dir / (self.get_uniqueish_name() + self.surface.suffix)
        color_cmd = self.preprocess_surface_cmd(tmp_colored)
        if color_cmd:
            sp.run(color_cmd)
            colored_surface = tmp_colored
        else:
            colored_surface = self.surface

        stats_cmd = self.generate_textblock_cmd()
        if stats_cmd:
            textblock = sp.run(stats_cmd, stdout=sp.PIPE).stdout
        else:
            textblock = ''

        return colored_surface, textblock


@dataclass(frozen=True)
class ColoredHemiPreparer(BaseHemiPreparer):
    """
    Wraps a surface file with a corresponding vertex-wise data file.

    It runs the commands ``colour_object`` and ``vertstats_stats``.
    """
    data_file: Path
    data_min: str
    data_max: str
    color_map: Optional[str]
    """
    See ``colour_object -help`

    ``color_map`` should be a ``typing.Literal``, but I am tired...

    color_map is one of:

        gray, hot, hot_inv, cold_metal, cold_metal_inv,
        green_metal, green_metal_inv, lime_metal, lime_metal_inv,
        red_metal, red_metal_inv, purple_metal, purple_metal_inv,
        spectral, red, green, blue, label, rgba
    """

    def preprocess_surface_cmd(self, output: Path) -> Optional[Sequence[str | os.PathLike]]:
        return 'colour_object', self.surface, self.data_file, output, self.color_map, self.data_min, self.data_max

    def generate_textblock_cmd(self) -> Optional[Sequence[str | os.PathLike]]:
        return 'vertstats_stats', self.data_file

    def get_uniqueish_name(self) -> str:
        parts = [self.surface.name, self.data_file.name, self.color_map, self.data_min, self.data_max]
        return '_'.join(map(str, parts))


@dataclass(frozen=True)
class SectionBuilder(Runnable[Section]):
    """
    Builder for ``DrawableBrain``.
    """

    left: BaseHemiPreparer
    right: BaseHemiPreparer

    def run(self, sp: Runner) -> Section:
        surface_left, textblock_left = self.left.run(sp)
        surface_right, textblock_right = self.right.run(sp)
        return Section(surface_left, surface_right, textblock_left, textblock_right)
