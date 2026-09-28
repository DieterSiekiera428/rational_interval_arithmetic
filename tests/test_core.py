import math
import unittest
from fractions import Fraction

from rational_interval_arithmetic import RInterval


class TestConstruction(unittest.TestCase):

    def test_basic_bounds(self):
        iv = RInterval("1/2", "3/4")
        self.assertEqual(iv.lo, Fraction(1, 2))
        self.assertEqual(iv.hi, Fraction(3, 4))

    def test_int_endpoints(self):
        iv = RInterval(-2, 3)
        self.assertEqual(iv.lo, -2)
        self.assertEqual(iv.hi, 3)

    def test_fraction_endpoints(self):
        iv = RInterval(Fraction(1, 3), Fraction(2, 3))
        self.assertEqual(iv.width(), Fraction(1, 3))

    def test_degenerate_point_interval(self):
        iv = RInterval.point("5/2")
        self.assertEqual(iv.lo, iv.hi)
        self.assertEqual(iv.lo, Fraction(5, 2))

    def test_equal_bounds_allowed(self):
        iv = RInterval(7, 7)
        self.assertEqual(iv.width(), 0)

    def test_inverted_bounds_raise(self):
        with self.assertRaises(ValueError):
            RInterval(5, 2)

    def test_float_rejected(self):
        with self.assertRaises(TypeError):
            RInterval(0.1, 0.2)
        with self.assertRaises(TypeError):
            RInterval.point(1.0)


class TestArithmetic(unittest.TestCase):

    def test_add(self):
        a = RInterval(1, 2)
        b = RInterval(3, 5)
        self.assertEqual(a + b, RInterval(4, 7))

    def test_add_with_scalar(self):
        self.assertEqual(RInterval(1, 2) + 3, RInterval(4, 5))

    def test_sub(self):
        a = RInterval(1, 4)
        b = RInterval(2, 3)
        self.assertEqual(a - b, RInterval(-2, 2))

    def test_sub_yields_negative(self):
        self.assertEqual(RInterval(1, 2) - RInterval(10, 20), RInterval(-19, -8))

    def test_mul_positive(self):
        self.assertEqual(RInterval(2, 3) * RInterval(4, 5), RInterval(8, 15))

    def test_mul_mixed_signs(self):
        # [-2, 3] * [-1, 4]: corners -8, -2, -3, 12 -> [-8, 12]
        self.assertEqual(RInterval(-2, 3) * RInterval(-1, 4), RInterval(-8, 12))

    def test_mul_both_negative(self):
        # [-5,-2] * [-4,-1]: corners 20, 5, 8, 2 -> [2, 20]
        self.assertEqual(RInterval(-5, -2) * RInterval(-4, -1), RInterval(2, 20))

    def test_mul_with_zero_crossing(self):
        # [-2, 3] * [0, 4]: corners 0, -8, 0, 12 -> [-8, 12]
        self.assertEqual(RInterval(-2, 3) * RInterval(0, 4), RInterval(-8, 12))

    def test_div_positive(self):
        # [1,2] / [3,4] = [1,2] * [1/4, 1/3] = [1/4, 2/3]
        self.assertEqual(RInterval(1, 2) / RInterval(3, 4),
                         RInterval(Fraction(1, 4), Fraction(2, 3)))

    def test_div_by_interval_containing_zero(self):
        with self.assertRaises(ZeroDivisionError):
            RInterval(1, 2) / RInterval(-1, 1)

    def test_div_by_point_zero(self):
        with self.assertRaises(ZeroDivisionError):
            RInterval(1, 2) / RInterval.point(0)

    def test_div_negative_denominator(self):
        # [6, 12] / [-3, -1] = [6,12] * [-1, -1/3] = [-12, -2]
        self.assertEqual(RInterval(6, 12) / RInterval(-3, -1),
                         RInterval(-12, -2))


class TestScale(unittest.TestCase):

    def test_scale_positive(self):
        self.assertEqual(RInterval(1, 2).scale(3), RInterval(3, 6))

    def test_scale_negative_swaps_bounds(self):
        self.assertEqual(RInterval(1, 4).scale(-2), RInterval(-8, -2))

    def test_scale_fraction(self):
        self.assertEqual(RInterval(2, 4).scale(Fraction(1, 2)), RInterval(1, 2))

    def test_scale_zero_collapses(self):
        self.assertEqual(RInterval(-5, 5).scale(0), RInterval.point(0))


class TestContainmentAndRelations(unittest.TestCase):

    def test_contains_inside(self):
        self.assertTrue(RInterval(1, 3).contains(2))

    def test_contains_endpoint_inclusive(self):
        iv = RInterval(1, 3)
        self.assertTrue(iv.contains(1))
        self.assertTrue(iv.contains(3))

    def test_contains_outside(self):
        self.assertFalse(RInterval(1, 3).contains(4))

    def test_in_operator_with_fraction(self):
        iv = RInterval("1/3", "2/3")
        self.assertIn(Fraction(1, 2), iv)
        self.assertNotIn(Fraction(1, 4), iv)

    def test_in_operator_rejects_non_rational(self):
        # __contains__ must not raise on unsupported types; it returns False.
        self.assertNotIn([1, 2, 3], RInterval(0, 1))
        self.assertNotIn(None, RInterval(0, 1))

    def test_intersects_overlapping(self):
        self.assertTrue(RInterval(1, 3).intersects(RInterval(2, 5)))

    def test_intersects_touching(self):
        self.assertTrue(RInterval(1, 2).intersects(RInterval(2, 3)))

    def test_intersects_disjoint(self):
        self.assertFalse(RInterval(1, 2).intersects(RInterval(3, 4)))

    def test_subset_true(self):
        self.assertTrue(RInterval(2, 3).is_subset_of(RInterval(1, 4)))

    def test_subset_equal(self):
        iv = RInterval(1, 2)
        self.assertTrue(iv.is_subset_of(iv))

    def test_subset_false(self):
        self.assertFalse(RInterval(0, 5).is_subset_of(RInterval(1, 4)))


class TestHull(unittest.TestCase):

    def test_hull_disjoint(self):
        h = RInterval.hull([RInterval(1, 2), RInterval(5, 6)])
        self.assertEqual(h, RInterval(1, 6))

    def test_hull_overlapping(self):
        h = RInterval.hull([RInterval(1, 4), RInterval(3, 7)])
        self.assertEqual(h, RInterval(1, 7))

    def test_hull_single(self):
        h = RInterval.hull([RInterval(1, 2)])
        self.assertEqual(h, RInterval(1, 2))

    def test_hull_empty_raises(self):
        with self.assertRaises(ValueError):
            RInterval.hull([])

    def test_hull_with_negative_bounds(self):
        h = RInterval.hull([RInterval(-5, -3), RInterval(-1, 2)])
        self.assertEqual(h, RInterval(-5, 2))


class TestMisc(unittest.TestCase):

    def test_midpoint(self):
        self.assertEqual(RInterval(1, 4).midpoint(), Fraction(5, 2))

    def test_width(self):
        self.assertEqual(RInterval("1/3", "2/3").width(), Fraction(1, 3))

    def test_equality_and_hash(self):
        a = RInterval(1, 2)
        b = RInterval("1", "2")
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

    def test_inequality(self):
        self.assertNotEqual(RInterval(1, 2), RInterval(1, 3))

    def test_repr_roundtrips(self):
        iv = RInterval(Fraction(1, 3), Fraction(2, 3))
        self.assertEqual(repr(iv), "RInterval(Fraction(1, 3), Fraction(2, 3))")

    def test_str_format(self):
        self.assertEqual(str(RInterval(1, 2)), "[1, 2]")

    def test_from_pair_alias(self):
        self.assertEqual(RInterval.from_pair(1, 2), RInterval(1, 2))


class TestExactness(unittest.TestCase):
    """The whole point: no floating-point drift on ugly decimals."""

    def test_decimal_string_addition_is_exact(self):
        a = RInterval("0.1", "0.2")
        b = RInterval("0.3", "0.4")
        result = a + b
        # Exact: 0.1 + 0.3 = 0.4, 0.2 + 0.4 = 0.6
        self.assertEqual(result.lo, Fraction(2, 5))
        self.assertEqual(result.hi, Fraction(3, 5))

    def test_thirds_arithmetic(self):
        a = RInterval("1/3", "2/3")
        b = RInterval("1/3", "2/3")
        prod = a * b
        self.assertEqual(prod.lo, Fraction(1, 9))
        self.assertEqual(prod.hi, Fraction(4, 9))


if __name__ == "__main__":
    unittest.main()
