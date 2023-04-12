"""
Here lies the code which puts everything together.

Note to developer: options such as colors and sizes should not be
hard-coded anywhere. Here is the only place where the values for
those options should be passed to the functions which accept them.
"""

from pathlib import Path
from typing import Sequence
from dataclasses import dataclass

from surfigures.draw import constants
from surfigures.draw.prep import SectionBuilder, BaseHemiPreparer, ColoredHemiPreparer
from surfigures.draw.section import RowPair
from surfigures.draw.tile import LazyTile
from surfigures.inputs.subject import SubjectSet
from surfigures.options import Options
from surfigures.util.runnable import Runnable, Runner


@dataclass(frozen=True)
class FigureCreator(Runnable[Path]):

    inputs: SubjectSet
    output_path: Path
    options: Options

    def run(self, sp: Runner) -> Path:
        mid_surface_left = self.inputs.mid_surface_left(sp)
        mid_surface_right = self.inputs.mid_surface_right(sp)

        figure_data: Sequence[SectionBuilder] = (
            *(
                SectionBuilder(
                    BaseHemiPreparer(layer.left),
                    BaseHemiPreparer(layer.right),
                )
                for layer in self.inputs.surfaces
            ),
            *(
                SectionBuilder(
                    ColoredHemiPreparer(
                        mid_surface_left,
                        files.left,
                        *self.options.range_for(files.left),
                        self.options.color_map
                    ),
                    ColoredHemiPreparer(
                        mid_surface_right,
                        files.right,
                        *self.options.range_for(files.right),
                        self.options.color_map
                    )
                )
                for files in self.inputs.data_files
            )
        )

        section_captions = [
            *(s.caption for s in self.inputs.surfaces),
            *(s.caption for s in self.inputs.data_files)
        ]

        figure_template = (f.run(sp) for f in figure_data)
        row_pairs = [f.to_row_pair() for f in figure_template]
        tile_grid = [row for rows in map(_rowpair2rows, row_pairs) for row in rows]
        """2D matrix of LazyTile"""
        lazy_tiles = [tile for row in tile_grid for tile in row]
        """1D flattened structure of data and order as tile_grid"""
        n_row = len(tile_grid)
        n_col = len(tile_grid[0])

        tile_files = [sp.tmp_dir / f'{i}_{section_captions[i // (n_col * 2)]}.rgb' for i in range(len(lazy_tiles))]

        for tile, name in zip(lazy_tiles, tile_files):
            cmd = tile.ray_trace.to_cmd(self.options.bg, constants.TILE_SIZE, constants.TILE_SIZE, name)
            sp.run(cmd)

        montage_file = sp.tmp_dir / 'montage_output.png'
        montage_cmd = (
            'montage',
            '-tile', f'{n_col}x{n_row}',
            '-background', self.options.bg,
            '-geometry', f'{constants.TILE_SIZE}x{constants.TILE_SIZE}+{constants.COL_CAP}+{constants.ROW_GAP}',
            *tile_files,
            montage_file
        )
        sp.run(montage_cmd)

        annotation_flags = []
        for row, row_tiles in enumerate(tile_grid):
            for col, tile in enumerate(row_tiles):
                annotation_flags.extend(tile.labels2args(
                    row, col,
                    constants.TILE_SIZE, constants.TILE_SIZE,
                    constants.COL_CAP, constants.ROW_GAP
                ))

        caption_x = round(constants.COL_CAP * 5 + constants.TILE_SIZE * 2 + 100)
        for i, caption in enumerate(section_captions):
            row = i * 2
            caption_y = round(constants.ROW_GAP * (0.5 + 2 * row) + constants.TILE_SIZE * row)
            annot = ['-annotate', f'0x0+{caption_x}+{caption_y}', caption]
            annotation_flags.extend(annot)

        convert_cmd = (
            'convert',
            '-box', self.options.bg,
            '-fill', self.options.font_color,
            '-pointsize', str(constants.FONT_SIZE),
            *annotation_flags,
            montage_file,
            self.output_path
        )
        sp.run(convert_cmd)

        return self.output_path


def _rowpair2rows(row_pair: RowPair) -> tuple[Sequence[LazyTile], Sequence[LazyTile]]:
    half = len(row_pair) // 2
    return row_pair[:half], row_pair[half:]
