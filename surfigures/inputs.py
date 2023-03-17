"""
Helper functions to find input files for ``verify_surface_all.pl``
based on naming conventions.
"""
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Iterator, Optional, Callable, Iterable, TypeVar, Generic
import subprocess as sp
from tempfile import NamedTemporaryFile

from loguru import logger
from chris_plugin import PathMapper

from surfigures.options import Options

LEFT_WORDS = ('left', 'Left', 'LEFT')
RIGHT_WORDS = ('right', 'Right', 'RIGHT')
SIDES: tuple[str, ...] = (*LEFT_WORDS, *RIGHT_WORDS)
SEPARATORS = ('-', '_', ' ')


@dataclass(frozen=True)
class WholeBrainLayer:
    caption: str
    left: Path
    right: Path


@dataclass(frozen=True)
class VertexDataFiles:
    caption: str
    left: Path
    right: Path


@dataclass(frozen=True)
class VertexDataGroup(VertexDataFiles):
    min: str
    max: str


def surfaces2row(s: WholeBrainLayer):
    return s.caption, s.left, s.right


def datas2row(d: VertexDataGroup):
    return d.caption, d.left, d.right, d.min, d.max


@dataclass(frozen=True)
class SortedInputs:
    title: str
    surfaces: Sequence[WholeBrainLayer]
    data: Sequence[VertexDataGroup]

    def to_cmd(self, output: Path) -> Sequence[str | Path]:
        return [
            'verify_surface_all.pl',
            self.title,
            output,
            *(arg for row in map(surfaces2row, self.surfaces) for arg in row),
            *(arg for row in map(datas2row, self.data) for arg in row)
        ]


@dataclass(frozen=True)
class InputSet:
    """
    (Unsorted) batch of inputs for ``verify_surfaces_all.pl``
    """

    title: str
    src: tuple[Path, ...]
    surfaces: Sequence[WholeBrainLayer]
    data_files: Sequence[VertexDataFiles]

    def expand(self, options: Options, tmp_dir: Path) -> SortedInputs:
        """
        Run the extra computations specified by ``options`` and then sort the inputs.
        """
        # TODO use surface-stats to sort inputs by surface area
        # for now, we depend on the arbitrary order given by Path.glob
        surfaces = self.surfaces
        data_files = [
            VertexDataGroup(f.caption, f.left, f.right, *options.range_for(f.left))
            for f in self.data_files
        ]
        data_files += self._abs(data_files, options.abs, tmp_dir)
        return SortedInputs(
            title=self.title,
            surfaces=surfaces,
            data=data_files
        )

    @staticmethod
    def _abs(data_files: list[VertexDataGroup], suffixes: Iterable[str], tmp_dir: Path) -> list[VertexDataGroup]:
        """
        For every data file which has a file extension that is one of the given suffixes,
        compute the absolute values to a file in ``tmp_dir``. Returns created files.
        """
        check_needs_abs = ((orig, abs_files(orig, suffixes, tmp_dir)) for orig in data_files)
        return [
            calc_abs(orig, result)
            for orig, result in check_needs_abs
            if result is not None
        ]

    @classmethod
    def from_folders(cls, left_folder: Path, right_folder: Path, data_file_suffix: str) -> 'InputSet':
        surface_pairs = cls._find_left_and_right_in_folders(left_folder, right_folder, '.obj')
        data_file_pairs = cls._find_left_and_right_in_folders(left_folder, right_folder, data_file_suffix)
        return cls(
            title=fname_without_side(left_folder),
            src=(left_folder, right_folder),
            surfaces=[WholeBrainLayer(l.name, l, r) for l, r in surface_pairs],
            data_files=[VertexDataFiles(l.name, l, r) for l, r in data_file_pairs]
        )

    @classmethod
    def from_folder(cls, folder: Path, data_file_suffix: str) -> 'InputSet':
        surface_pairs = cls._find_left_and_right_files(folder, '.obj')
        data_file_pairs = cls._find_left_and_right_files(folder, data_file_suffix)
        return cls(
            title=folder.name,
            src=(folder,),
            surfaces=[WholeBrainLayer(fname_without_side(l), l, r) for l, r in surface_pairs],
            data_files=[VertexDataFiles(fname_without_side(l), l, r) for l, r in data_file_pairs]
        )

    @staticmethod
    def _find_left_and_right_in_folders(left_folder: Path, right_folder: Path, ext: str) -> Sequence[tuple[Path, Path]]:
        # file names in left and right folders must be *exactly* the same.
        # TODO tolerate "left" and "right" substrings being in path names
        pairs = [
            (left_file, right_folder / left_file.name)
            for left_file in left_folder.glob(f'*{ext}')
        ]
        return validate_pairs(pairs)

    @staticmethod
    def _find_left_and_right_files(folder: Path, ext: str) -> Sequence[tuple[Path, Path]]:
        left_files = find_side_files(folder, ext, LEFT_WORDS)
        pairs = find_right_files_for(left_files)
        return validate_pairs(pairs)


def calc_abs(orig: VertexDataGroup, result: VertexDataGroup) -> VertexDataGroup:
    for files in ((orig.left, result.left), (orig.right, result.right)):
        cmd = ('vertstats_math', '-old_style_file', '-abs', *files)
        str_cmd = shlex.join(map(str, cmd))
        logger.info('running: {}', str_cmd)
        p = sp.run(cmd, stdout=sp.DEVNULL, stderr=sp.STDOUT)
        if p.returncode != 0:
            raise InputError(f'Command failed: {str_cmd}')
    return result


def abs_files(g: VertexDataGroup, suffixes: Iterable[str], tmp_dir: Path) -> Optional[VertexDataGroup]:
    """
    If the abs function should be applied to the files of ``g``,
    return file names for where the output files should be written to.
    """
    for suffix in suffixes:
        left = name_tempfile_if_endswith(g.left, suffix, '.abs', tmp_dir)
        right = name_tempfile_if_endswith(g.right, suffix, '.abs', tmp_dir)
        if left and right:
            return VertexDataGroup(g.caption, left, right, '0.0', g.max)
    return None


def name_tempfile_if_endswith(path: Path, suffix: str, prefix_for_suffix: str, tmp_dir: Path) -> Optional[Path]:
    s = path.name.rsplit(suffix, maxsplit=1)
    if len(s) != 2:
        return None
    stem, _ = s
    parent = tmp_dir / path.parent.name
    parent.mkdir(exist_ok=True)
    return parent / (stem + prefix_for_suffix + suffix)


def find_side_files(folder: Path, ext: str, sides: Iterable[str] = ('',)) -> Iterator[Path]:
    for side in sides:
        yield from folder.glob(f'*{side}*{ext}')


def find_right_files_for(left_files: Iterator[Path]) -> Sequence[tuple[Path, Optional[Path]]]:
    return list(_find_right_files_for_generator(left_files))


def _find_right_files_for_generator(left_files: Iterator[Path]) -> Iterator[tuple[Path, Optional[Path]]]:
    for left_file in left_files:
        yield left_file, corresponding_right_path_to(left_file)


def fname_without_side(path: Path) -> str:
    name = path.name
    for side in SIDES:
        start = name.find(side)
        if start == -1:
            continue
        end = start + len(side)
        if start - 1 >= 0 and name[start - 1] in SEPARATORS:
            start -= 1
        if start == 0 and name[end] in SEPARATORS:
            end += 1
        return name[:start] + name[end:]
    raise InputError(f'File name of {path} does not contain "left" nor "right"')


def validate_pairs(pairs: Sequence[tuple[Path, Optional[Path]]]) -> Sequence[tuple[Path, Path]]:
    for left, right in pairs:
        if not left.is_file():
            raise InputError(f'"{left}" is not a file')
        if right is None:
            raise InputError(f'No corresponding right-sided file found for left-sided file "{left}"')
        if not right.is_file():
            raise InputError(f'"{right}" is not a file')
    return pairs


@dataclass(frozen=True)
class InputSetBuilder:
    """
    Helper to curry the ``data_file_suffix`` of ``InputSet`` constructors.
    """
    data_file_suffix: str

    def from_folders(self, left_folder: Path, right_folder: Path) -> InputSet:
        return InputSet.from_folders(left_folder, right_folder, self.data_file_suffix)

    def from_folder(self, folder: Path) -> InputSet:
        return InputSet.from_folder(folder, self.data_file_suffix)


class InputError(Exception):
    """
    Input files not found or not suitable.
    """
    pass


_T = TypeVar('_T')
_R = TypeVar('_R')


@dataclass(frozen=True)
class InputMonad(Generic[_T]):
    """
    Fancy functional programming pattern for propagating errors from within a generator
    then continuing iteration without ``raise`` (which would end the loop).
    """
    inner: _T | InputError

    @classmethod
    def wrap(cls, f: Callable[[], _T]) -> 'InputMonad[_T]':
        try:
            inner = f()
        except InputError as e:
            inner = e
        return cls(inner)

    @classmethod
    def new_err(cls, why):
        return cls(InputError(why))

    def map(self, f: Callable[[_T], _R]) -> 'InputMonad[_R]':
        if self.is_err():
            return self
        return InputMonad(f(self.inner))

    def starmap(self, f: Callable[..., _R]) -> 'InputMonad[_R]':
        if self.is_err():
            return self
        return InputMonad(f(*self.inner))

    def is_err(self):
        return isinstance(self.inner, InputError)

    def unwrap(self) -> _T:
        if self.is_err():
            raise self.inner
        return self.inner


@dataclass(frozen=True)
class InputFinder:
    input_dir: Path
    output_dir: Path

    def map(self, data_file_suffix: str, output_template: str
            ) -> Iterator[tuple[Optional[tuple[InputSet, Path]], Optional[InputError]]]:
        """
        Find inputs for ``verify_surface_all.pl`` and yield them along with a path for an output file.

        This is an awkward generator which yields a union data type in the form of a two-tuple.

        Usable sets of input files are yielded as ``(input_set, output_file_path), None``
        whereas inputs which must be skipped are yielded as ``None, InputError``.
        """
        for maybe_inputs, sub_output in self._map_sided_and_everything_folders(data_file_suffix):
            try:
                inputs = maybe_inputs.unwrap()
                output_file = sub_output.with_name(output_template.replace('{}', inputs.title))
                yield (inputs, output_file), None
            except InputError as e:
                yield None, e

    def _map_sided_and_everything_folders(self, data_file_suffix: str) -> Iterator[tuple[InputMonad[InputSet], Path]]:
        inputs_builder = InputSetBuilder(data_file_suffix)
        for maybe_pair, sub_output in self._sided_folders_mapper():
            yield InputMonad(maybe_pair).starmap(inputs_builder.from_folders), sub_output
        for subject_folder, sub_output in self._subject_folders_mapper():
            yield InputMonad.wrap(lambda: inputs_builder.from_folder(subject_folder)), sub_output

    def _sided_folders_mapper(self) -> Iterator[tuple[tuple[Path, Path] | InputError, Path]]:
        left_folder_mapper = PathMapper.dir_mapper_deep(self.input_dir, self.output_dir,
                                                        filter=is_left_folder_containing_obj)
        for left_folder, sub_output in left_folder_mapper:
            right_folder = corresponding_right_path_to(left_folder)
            if right_folder is None:
                pair = InputError('Cannot find folder for right-sided inputs '
                                  f'corresponding to left folder "{left_folder}"')
            else:
                pair = left_folder, right_folder
            yield pair, sub_output

    def _subject_folders_mapper(self) -> Iterator[tuple[Path, Path]]:
        mapper = PathMapper.dir_mapper_deep(self.input_dir, self.output_dir, filter=is_unsided_subjects_folder)
        return iter(mapper)


def is_left_folder_containing_obj(folder: Path) -> bool:
    return contains_obj(folder) and is_side_folder(folder, 'left')


def is_unsided_subjects_folder(folder: Path) -> bool:
    return contains_obj(folder) and not any(is_side_folder(folder, side) for side in SIDES)


def contains_obj(folder: Path) -> bool:
    return next(folder.glob('*.obj'), None) is not None


def is_side_folder(folder: Path, side: str) -> bool:
    return side.lower() in folder.name.lower()


def corresponding_right_path_to(path: Path) -> Optional[Path]:
    possible_paths = map(lambda l, r: path.with_name(path.name.replace(l, r)), LEFT_WORDS, RIGHT_WORDS)
    possible_right_paths = filter(lambda p: 'right' in p.name.lower(), possible_paths)
    existing_right_paths = filter(lambda f: f.exists(), possible_right_paths)
    return next(existing_right_paths, None)
