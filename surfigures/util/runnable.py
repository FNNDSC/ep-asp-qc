import abc
import os
from pathlib import Path
from typing import Generic, TypeVar, Sequence
import subprocess as sp

T = TypeVar('T')


class Runner(abc.ABC):
    """
    For the most part, ``Runnable`` are wrappers to the ``subprocess`` module.
    """

    STDOUT = sp.STDOUT
    DEVNULL = sp.DEVNULL
    PIPE = sp.PIPE

    @property
    @abc.abstractmethod
    def tmp_dir(self) -> Path:
        """
        A temporary directory, a suitable location for output files.
        """
        ...

    @abc.abstractmethod
    def run(self, cmd: Sequence[str | os.PathLike], stdout=sp.DEVNULL, stderr=sp.DEVNULL) -> sp.CompletedProcess:
        ...


class Runnable(abc.ABC, Generic[T]):
    """
    A ``Runnable`` is a set of inputs which can be transformed into outputs by running subprocesses.

    In retrospect, this abstraction was a bad idea.
    """

    @abc.abstractmethod
    def run(self, sp: Runner) -> T:
        """
        :param sp: can be used to run subcommands and capture subcommand output
        :returns: an object which represents the created output
        """
        ...
