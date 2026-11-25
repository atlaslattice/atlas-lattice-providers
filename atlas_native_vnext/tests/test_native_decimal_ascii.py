"""Synthetic scientific quantity wire-grammar regressions; no host/API calls."""
import importlib.util
from decimal import Decimal
from pathlib import Path
import unittest

WIRE_PATH = Path(__file__).resolve().parents[1] / 'native_synthesis' / 'wire.py'
SPEC = importlib.util.spec_from_file_location('atlas_native_wire_decimal_only', WIRE_PATH)
wire = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wire)


class ASCIIQuantityBoundary(unittest.TestCase):
    def test_ascii_integer(self):
        self.assertEqual(wire.exact_quantity('42', 'count'), Decimal('42'))

    def test_ascii_signed_fraction(self):
        self.assertEqual(wire.exact_quantity('-0.125', 'J'), Decimal('-0.125'))

    def test_ascii_scientific_exponent(self):
        self.assertEqual(wire.exact_quantity('1.2e-100', 'J'), Decimal('1.2e-100'))

    def test_unicode_decimal_mantissa_is_held(self):
        for raw in ('1.٢', '١.2', '9٩', '３.1', '1.２'):
            with self.subTest(raw=repr(raw)), self.assertRaises(wire.WireError):
                wire.exact_quantity(raw, 'J')

    def test_unicode_decimal_exponent_is_held(self):
        for raw in ('1e+٩', '1e۹', '1e-１', '1.2e٣'):
            with self.subTest(raw=repr(raw)), self.assertRaises(wire.WireError):
                wire.exact_quantity(raw, 'Hz')

    def test_invalid_unicode_minus_is_held(self):
        with self.assertRaises(wire.WireError):
            wire.exact_quantity('−2', 'J')

    def test_nonfinite_and_json_float_style_not_accepted(self):
        for raw in ('NaN', 'Infinity', '1.0.0', '1e1000'):
            with self.subTest(raw=raw), self.assertRaises(wire.WireError):
                wire.exact_quantity(raw, 'J')

    def test_units_still_mandatory(self):
        for unit in ('', 'unknown', 'joule', 'kg/s'):
            with self.subTest(unit=unit), self.assertRaises(wire.WireError):
                wire.exact_quantity('1.5', unit)

    def test_binary_float_input_not_accepted(self):
        with self.assertRaises(wire.WireError):
            wire.exact_quantity(1.5, 'J')

    def test_mantissa_precision_limit_retained(self):
        with self.assertRaises(wire.WireError):
            wire.exact_quantity('9' * 43, 'J')

    def test_exponent_magnitude_limit_retained(self):
        with self.assertRaises(wire.WireError):
            wire.exact_quantity('1e251', 'J')


if __name__ == '__main__':
    unittest.main()
