# Rational Interval Arithmetic

A small Python library for computing guaranteed bounds on arithmetic over closed intervals whose endpoints are exact rationals (via `fractions.Fraction`).

## Usage

```python
from rational_interval_arithmetic import RInterval

a = RInterval("1/3", "2/3")
b = RInterval("-1", "1")
print(a + b)          # [-2/3, 5/3]
print(a * b)          # [-2/3, 2/3]
print(a.scale(-2))    # [-4/3, -2/3]

print(RInterval(1, 2) / RInterval(3, 4))  # [1/4, 2/3]

print(RInterval.hull([RInterval(0, 1), RInterval(3, 4)]))  # [0, 4]
```

## Exported names

- `RInterval` — the interval class.

### `RInterval(lo, hi)`
Construct `[lo, hi]`. `lo` and `hi` may be `int`, `str` (e.g. `"1/3"`, `"0.1"`), or `Fraction`. `float` is rejected. Raises `ValueError` if `lo > hi`.

### Properties
- `.lo`, `.hi` — exact `Fraction` endpoints.

### Methods
- `.contains(x)` — inclusive membership; `x in iv` also works (returns `False` for unsupported types rather than raising).
- `.intersects(other)` — closed-interval overlap test.
- `.is_subset_of(other)`
- `.scale(k)` — multiply by an exact scalar; negative `k` swaps the bounds.
- `.width()`, `.midpoint()` — both return `Fraction`.
- `.hull(intervals)` (classmethod) — smallest interval containing all inputs; empty iterable raises `ValueError`.
- `.point(x)` (classmethod) — degenerate `[x, x]`.
- `.from_pair(lo, hi)` (classmethod) — constructor alias.

### Operators
`+`, `-`, `*`, `/` between two `RInterval`s (or an `RInterval` and a bare rational). `==` and `hash()` compare exact endpoints.

## Why this exists

Floating-point interval arithmetic gives bounds that are themselves slightly fuzzy because the endpoint rounding is in floating point. When you need a *guaranteed* enclosure — for a proof, a verified computation, or just to avoid subtle drift — the endpoints themselves must be exact. `fractions.Fraction` gives that, at the cost of speed: rational arithmetic is slower than float and the numerators/denominators grow. This library makes that trade deliberately and does not apologise for it.

## The awkward edge

Division by an interval that contains zero is undefined here and raises `ZeroDivisionError`. There is no `[-inf, inf]` convention. If you need extended-real intervals, this is not the library for it.

Also: `float` inputs are rejected on construction. A `float` like `0.1` is already a binary approximation; silently admitting it would defeat the purpose. Pass `"0.1"` or `Fraction(1, 10)`.
