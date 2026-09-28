from __future__ import annotations

from fractions import Fraction
from typing import Union, Iterable

# A rational number or anything Fraction() accepts: int, str like "1/3", float, Fraction.
RationalLike = Union[int, str, Fraction, float]


def _to_fraction(value: RationalLike) -> Fraction:
    """Convert any supported input to an exact Fraction.

    We explicitly reject float inputs because floats are the very imprecision
    this library exists to avoid. Accepting a float would silently import a
    binary-approximate value into a library whose entire contract is exactness.
    Callers who really mean a float can pass str(float) and accept the
    decimal-string rounding, or construct a Fraction manually.
    """
    if isinstance(value, float):
        raise TypeError(
            "RInterval does not accept float directly; it would import "
            "binary-approximate values. Pass a Fraction, int, or decimal "
            "string like '0.1' instead."
        )
    return Fraction(value)


class RInterval:
    """A closed interval [lo, hi] with exact rational endpoints.

    All arithmetic is performed with fractions.Fraction so the endpoints are
    always exact. Each binary operation returns a new RInterval whose endpoints
    are the true minimum and maximum of the result over all points in the
    input intervals — a *guaranteed* enclosure, not an approximation.

    The interval is closed ([lo, hi], not (lo, hi)) because rational endpoints
    are exactly representable and there is no reason to exclude them. Division
    by an interval containing zero raises ZeroDivisionError; there is no
    extended-real convention here.
    """

    __slots__ = ("_lo", "_hi")

    def __init__(self, lo: RationalLike, hi: RationalLike):
        a = _to_fraction(lo)
        b = _to_fraction(hi)
        if a > b:
            raise ValueError(
                f"interval lower bound {a} exceeds upper bound {b}"
            )
        self._lo = a
        self._hi = b

    # ---- properties -------------------------------------------------

    @property
    def lo(self) -> Fraction:
        return self._lo

    @property
    def hi(self) -> Fraction:
        return self._hi

    # ---- containment & comparison -----------------------------------

    def contains(self, x: RationalLike) -> bool:
        """True if x is inside [lo, hi] (endpoints inclusive)."""
        v = _to_fraction(x)
        return self._lo <= v <= self._hi

    def __contains__(self, x: object) -> bool:
        if not isinstance(x, (int, str, Fraction)):
            return False
        return self.contains(x)  # type: ignore[arg-type]

    def intersects(self, other: "RInterval") -> bool:
        """Two closed intervals overlap iff neither is strictly past the other."""
        return not (self._hi < other._lo or other._hi < self._lo)

    def is_subset_of(self, other: "RInterval") -> bool:
        """True if every point of self lies inside other."""
        return other._lo <= self._lo and self._hi <= other._hi

    # ---- core arithmetic --------------------------------------------

    def __add__(self, other: "RInterval") -> "RInterval":
        o = _coerce(other)
        return RInterval(self._lo + o._lo, self._hi + o._hi)

    def __sub__(self, other: "RInterval") -> "RInterval":
        o = _coerce(other)
        # [a,b] - [c,d] = [a-d, b-c]. Subtraction reverses endpoint order.
        return RInterval(self._lo - o._hi, self._hi - o._lo)

    def __mul__(self, other: "RInterval") -> "RInterval":
        o = _coerce(other)
        # Four corner products; the enclosure is their min and max. Fraction
        # multiplication is exact, so no rounding enters.
        p1 = self._lo * o._lo
        p2 = self._lo * o._hi
        p3 = self._hi * o._lo
        p4 = self._hi * o._hi
        return RInterval(min(p1, p2, p3, p4), max(p1, p2, p3, p4))

    def __truediv__(self, other: "RInterval") -> "RInterval":
        o = _coerce(other)
        if o._lo <= 0 <= o._hi:
            raise ZeroDivisionError(
                "division by an interval containing zero is undefined "
                "(no extended-real convention)"
            )
        # If 0 is not in [c,d] the reciprocal is [1/d, 1/c]; then multiply.
        inv = RInterval(Fraction(1) / o._hi, Fraction(1) / o._lo)
        return self * inv

    # ---- scalar scaling ---------------------------------------------

    def scale(self, k: RationalLike) -> "RInterval":
        """Multiply by an exact rational scalar.

        A negative scalar swaps the endpoints; we handle it explicitly rather
        than routing through __mul__ so the branch is visible and testable.
        """
        s = _to_fraction(k)
        if s >= 0:
            return RInterval(self._lo * s, self._hi * s)
        return RInterval(self._hi * s, self._lo * s)

    # ---- misc -------------------------------------------------------

    def width(self) -> Fraction:
        return self._hi - self._lo

    def midpoint(self) -> Fraction:
        return (self._lo + self._hi) / 2

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RInterval):
            return NotImplemented
        return self._lo == other._lo and self._hi == other._hi

    def __hash__(self) -> int:
        return hash((self._lo, self._hi))

    def __repr__(self) -> str:
        return f"RInterval({self._lo!r}, {self._hi!r})"

    def __str__(self) -> str:
        return f"[{self._lo}, {self._hi}]"

    # Constructors ----------------------------------------------------

    @classmethod
    def point(cls, x: RationalLike) -> "RInterval":
        """A degenerate interval [x, x]."""
        return cls(x, x)

    @classmethod
    def from_pair(cls, lo: RationalLike, hi: RationalLike) -> "RInterval":
        """Alias for the constructor, for readability at call sites."""
        return cls(lo, hi)

    @classmethod
    def hull(cls, intervals: Iterable["RInterval"]) -> "RInterval":
        """Smallest interval containing every input interval.

        Empty iterable raises ValueError rather than returning a nonsense
        interval, since there is no identity element for a hull over rationals.
        """
        items = list(intervals)
        if not items:
            raise ValueError("hull of an empty iterable is undefined")
        lo = min(i._lo for i in items)
        hi = max(i._hi for i in items)
        return cls(lo, hi)


def _coerce(other: Union["RInterval", RationalLike]) -> "RInterval":
    """Accept either an RInterval or a bare rational for binary ops.

    Letting `interval + 3` work keeps the API ergonomic; we wrap the scalar in
    a point interval so the arithmetic code has exactly one path.
    """
    if isinstance(other, RInterval):
        return other
    return RInterval.point(other)
