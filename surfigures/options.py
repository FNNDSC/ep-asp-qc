from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class Options:
    abs: Sequence[str]
    range: dict[str, tuple[str, str]]
    min: str
    max: str

    @classmethod
    def from_args(cls, args) -> 'Options':
        return cls(
            abs=args.abs.split(','),
            range={s: (a, b) for s, a, b in map(_parse_range_arg, args.range.split(','))},
            min=args.min,
            max=args.max
        )

    def range_for(self, data_file: Path) -> tuple[str, str]:
        for suffix, range in self.range.items():
            if data_file.name.endswith(suffix):
                return range
        return self.min, self.max


def _parse_range_arg(s) -> tuple[str, str, str]:
    t = s.strip().split(':')
    if len(t) != 3:
        raise ValueError(f'Invalid value for --range: "{s}" is not in the form name:min:max')
    return t
