from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Layer:
    """
    A pair of left and right brain surfaces.
    """
    caption: str
    left: Path
    right: Path


@dataclass(frozen=True)
class DataFiles:
    """
    Vertex-wise data files for left and right brain surfaces.
    """
    caption: str
    left: Path
    right: Path
