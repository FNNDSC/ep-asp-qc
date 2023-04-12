import os
import subprocess
from pathlib import Path
import shlex
import subprocess as sp
import time
from tempfile import TemporaryDirectory
from typing import Optional, Sequence, TextIO

from loguru import logger

from surfigures.draw.fig import FigureCreator
from surfigures.inputs.subject import SubjectSet
from surfigures.options import Options
from surfigures.util.runnable import Runner


def run_surfigures(input_set: SubjectSet, output_file: Path, options: Options) -> Optional[float]:
    """
    :returns: ``None`` if there was an error, or the time spent running ``verify_surface_all.pl`` in seconds.
    """
    start = time.monotonic_ns()
    sorted_inputs = input_set.sort()
    fig = FigureCreator(sorted_inputs, output_file, options)
    log_path = output_file.with_suffix('.log')
    with TemporaryDirectory() as tmp_dir, log_path.open('w') as log_handle:
        runner = LoggedRunner(Path(tmp_dir), log_handle)
        ok = True
        try:
            fig.run(runner)
        except sp.CalledProcessError:
            ok = False

    end = time.monotonic_ns()
    elapsed = (end - start) / 1e9
    msg = f'{tuple(map(str, input_set.src))} --> {output_file} took {elapsed:.1f}s'
    if ok:
        logger.info(msg)
        return elapsed
    else:
        logger.error('{}. !!!FAILED!!! please check {}', msg, log_path)
        return None


class LoggedRunner(Runner):

    def __init__(self, tmp_dir: Path, log_file: TextIO):
        self.__tmp_dir = tmp_dir
        self.__log_file = log_file

    @property
    def tmp_dir(self) -> Path:
        return self.__tmp_dir

    def run(self, cmd: Sequence[str | os.PathLike], stdout=sp.DEVNULL, stderr=sp.DEVNULL) -> sp.CompletedProcess:
        self.__log_file.write(shlex.join(map(str, cmd)))
        self.__log_file.write('\n')
        return subprocess.run(cmd, stdout=stdout, stderr=stderr, check=True, text=True)
