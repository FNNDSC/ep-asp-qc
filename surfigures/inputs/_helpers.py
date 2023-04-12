from dataclasses import dataclass
from typing import Generic, TypeVar, Callable

from surfigures.inputs.err import InputError

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

    def is_err(self) -> bool:
        return isinstance(self.inner, InputError)

    def unwrap(self) -> _T:
        if self.is_err():
            raise self.inner
        return self.inner
