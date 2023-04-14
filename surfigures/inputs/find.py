"""
Helper functions to find input files.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Iterator, Optional, Iterable

from chris_plugin import PathMapper

import surfigures.inputs.constants as constants
from surfigures.inputs.err import InputError
from surfigures.inputs._helpers import InputMonad
from surfigures.inputs.groups import Layer, DataFiles
from surfigures.inputs.subject import SubjectSet


@dataclass(frozen=True)
class SubjectMapper:
    """
    A class with methods for finding subject input files in an input directory,
    and mapping them to output file names in an output directory.
    """
    input_dir: Path
    output_dir: Path

    def map(self, data_file_suffix: str, output_template: str
            ) -> Iterator[tuple[Optional[tuple[SubjectSet, Path]], Optional[InputError]]]:
        """
        Find inputs subject-wise and yield them along with a path for an output file.

        This is an (awkward) generator which yields a union data type in the form of a two-tuple.

        Usable sets of input files are yielded as ``(input_set, output_file_path), None``
        whereas inputs which must be skipped are yielded as ``None, InputError``.
        """
        for maybe_inputs, sub_output in self._map_sided_and_everything_folders(data_file_suffix):
            try:
                inputs = maybe_inputs.unwrap()
                output_file = self._name_output_file(inputs.title, sub_output, output_template)
                yield (inputs, output_file), None
            except InputError as e:
                yield None, e

    def _name_output_file(self, title: str, sub_output: Path, output_template: str) -> Path:
        if sub_output == self.output_dir:
            # handle in case inputdir is a subjects folder containing left and right hemis
            return self.output_dir / output_template.replace('{}', title)
        return sub_output.with_name(output_template.replace('{}', title))

    def _map_sided_and_everything_folders(self, data_file_suffix: str) -> Iterator[tuple[InputMonad[SubjectSet], Path]]:
        inputs_builder = _SubjectSetFinder(data_file_suffix)
        for maybe_pair, sub_output in self._sided_folders_mapper():
            yield InputMonad(maybe_pair).starmap(inputs_builder.in_folders), sub_output
        for subject_folder, sub_output in self._subject_folders_mapper():
            yield InputMonad.wrap(lambda: inputs_builder.in_folder(subject_folder)), sub_output

    def _sided_folders_mapper(self) -> Iterator[tuple[tuple[Path, Path] | InputError, Path]]:
        left_folder_mapper = PathMapper.dir_mapper_deep(self.input_dir, self.output_dir,
                                                        fail_if_empty=False,
                                                        filter=_is_left_folder_containing_obj)
        for left_folder, sub_output in left_folder_mapper:
            right_folder = _corresponding_right_path_to(left_folder)
            if right_folder is None:
                pair = InputError('Cannot find folder for right-sided inputs '
                                  f'corresponding to left folder "{left_folder}"')
            else:
                pair = left_folder, right_folder
            yield pair, sub_output

    def _subject_folders_mapper(self) -> Iterator[tuple[Path, Path]]:
        mapper = PathMapper.dir_mapper_deep(self.input_dir, self.output_dir,
                                            fail_if_empty=False,
                                            filter=_is_unsided_subjects_folder)
        return iter(mapper)


@dataclass(frozen=True)
class _SubjectSetFinder:
    """
    Namespace of curried helper functions to find input files of a single subject.
    """
    data_file_suffix: str

    def in_folders(self, left_folder: Path, right_folder: Path) -> SubjectSet:
        """
        Find left/right pairs of input files for one subject from two folders.
        """
        surface_pairs = _find_left_and_right_in_folders(left_folder, right_folder, '.obj')
        data_file_pairs = _find_left_and_right_in_folders(left_folder, right_folder, self.data_file_suffix)
        return SubjectSet(
            title=_fname_without_side(left_folder),
            src=(left_folder, right_folder),
            surfaces=[Layer(l.name, l, r) for l, r in surface_pairs],
            data_files=[DataFiles(l.name, l, r) for l, r in data_file_pairs]
        )

    def in_folder(self, folder: Path) -> SubjectSet:
        """
        Find left/right pairs of input files under a folder, where left and right data files are found
        in the same folder by similar names.
        """
        surface_pairs = _find_left_and_right_files(folder, '.obj')
        data_file_pairs = _find_left_and_right_files(folder, self.data_file_suffix)
        return SubjectSet(
            title=folder.name,
            src=(folder,),
            surfaces=[Layer(_fname_without_side(l), l, r) for l, r in surface_pairs],
            data_files=[DataFiles(_fname_without_side(l), l, r) for l, r in data_file_pairs]
        )


def _find_side_files(folder: Path, ext: str, sides: Iterable[str] = ('',)) -> Iterator[Path]:
    for side in sides:
        yield from folder.glob(f'*{side}*{ext}')


def _find_right_files_for(left_files: Iterator[Path]) -> Sequence[tuple[Path, Optional[Path]]]:
    return list(_find_right_files_for_generator(left_files))


def _find_right_files_for_generator(left_files: Iterator[Path]) -> Iterator[tuple[Path, Optional[Path]]]:
    for left_file in left_files:
        yield left_file, _corresponding_right_path_to(left_file)


def _fname_without_side(path: Path) -> str:
    name = path.name
    for side in constants.SIDES:
        start = name.find(side)
        if start == -1:
            continue
        end = start + len(side)
        if start - 1 >= 0 and name[start - 1] in constants.SEPARATORS:
            start -= 1
        if start == 0 and name[end] in constants.SEPARATORS:
            end += 1
        return name[:start] + name[end:]
    raise InputError(f'File name of {path} does not contain "left" nor "right"')


def _validate_pairs(pairs: Sequence[tuple[Path, Optional[Path]]]) -> Sequence[tuple[Path, Path]]:
    for left, right in pairs:
        if not left.is_file():
            raise InputError(f'"{left}" is not a file')
        if right is None:
            raise InputError(f'No corresponding right-sided file found for left-sided file "{left}"')
        if not right.is_file():
            raise InputError(f'"{right}" is not a file')
    return pairs


def _find_left_and_right_in_folders(left_folder: Path, right_folder: Path, ext: str) -> Sequence[tuple[Path, Path]]:
    # file names in left and right folders must be *exactly* the same.
    # TODO tolerate "left" and "right" substrings being in path names
    pairs = [
        (left_file, right_folder / left_file.name)
        for left_file in left_folder.glob(f'*{ext}')
    ]
    return _validate_pairs(pairs)


def _find_left_and_right_files(folder: Path, ext: str) -> Sequence[tuple[Path, Path]]:
    left_files = _find_side_files(folder, ext, constants.LEFT_WORDS)
    pairs = _find_right_files_for(left_files)
    return _validate_pairs(pairs)


def _is_left_folder_containing_obj(folder: Path) -> bool:
    return _contains_obj(folder) and _is_side_folder(folder, 'left')


def _is_unsided_subjects_folder(folder: Path) -> bool:
    return _contains_obj(folder) and not any(_is_side_folder(folder, side) for side in constants.SIDES)


def _contains_obj(folder: Path) -> bool:
    return next(folder.glob('*.obj'), None) is not None


def _is_side_folder(folder: Path, side: str) -> bool:
    return side.lower() in folder.name.lower()


def _corresponding_right_path_to(path: Path) -> Optional[Path]:
    possible_paths = map(lambda l, r: path.with_name(path.name.replace(l, r)), constants.LEFT_WORDS, constants.RIGHT_WORDS)
    existing_right_paths = filter(lambda f: f.exists() and f != path, possible_paths)
    return next(existing_right_paths, None)
