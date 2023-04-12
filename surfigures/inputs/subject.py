import dataclasses
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Self, Iterable

from loguru import logger

from surfigures.inputs.err import InputError
from surfigures.inputs.groups import Layer, DataFiles
from surfigures.util.runnable import Runner


@dataclass(frozen=True)
class SubjectSet:
    """
    Batch of input files for one subject.
    """

    title: str
    src: tuple[Path, ...]
    surfaces: list[Layer]
    data_files: list[DataFiles]

    def sort(self) -> Self:
        """
        Sort the surfaces from outer to inner.
        """
        surfaces = self.surfaces.copy()
        surfaces.sort(key=_surface_area_of_left, reverse=True)
        return dataclasses.replace(self, surfaces=surfaces)

    def surfaces_left(self) -> Iterable[Path]:
        return (layer.left for layer in self.surfaces)

    def surfaces_right(self) -> Iterable[Path]:
        return (layer.right for layer in self.surfaces)

    def mid_surface_left(self, sp: Runner) -> Path:
        return self._mid_surface_of(sp, 'left', self.surfaces_left())

    def mid_surface_right(self, sp: Runner) -> Path:
        return self._mid_surface_of(sp, 'right', self.surfaces_right())

    def _mid_surface_of(self, sp: Runner, suffix: str, surfaces: Iterable[Path]) -> Path:
        name = sp.tmp_dir / f'{self.title}_{suffix}.obj'
        sp.run(('average_surfaces', name, 'none', 'none', '1', *surfaces))
        return name

def _surface_area_of_left(layer: Layer) -> float:
    cmd = ('surface-stats', '-face_area', layer.left)
    str_cmd = shlex.join(map(str, cmd))
    p = subprocess.run(cmd, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise InputError(f'Command failed: {str_cmd}')
    try:
        area = float(p.stderr.rsplit('=', 1)[-1].strip())
    except ValueError:
        raise InputError(f'Unable to parse output from command: {str_cmd} :::: output: {p.stderr}')
    logger.info('running: {} => Total Surface Area = {}', str_cmd, area)
    return area
