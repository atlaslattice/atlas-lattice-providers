"""Exact public synthetic quantity bounds must not depend on Decimal context."""
import copy
import json
import pathlib
import sys
import unittest
from decimal import Inexact, Overflow, Rounded, Underflow, localcontext

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from labs.atlas_labs_v32 import prepare

DENIED = {"status": "HOLD", "reason": "INVALID_OR_UNAUTHORIZED_PUBLIC_SOURCE",
          "source_count": 0, "candidate": None}


def fixture():
    return json.loads((ROOT / 'examples/atlas_labs_v32_synthetic.json').read_text())


class DecimalContextTests(unittest.TestCase):
    def test_outside_bounds_hold_under_low_precision(self):
        for field in ('value', 'uncertainty'):
            for value in ('1000000000000.1', '9.999999999999e-13'):
                record = fixture()
                record['quantities'][0][field] = value
                for raw in (record, json.dumps(record)):
                    with self.subTest(field=field, value=value, raw=type(raw).__name__):
                        with localcontext() as context:
                            context.prec = 6
                            self.assertEqual(prepare(raw), DENIED)

    def test_exact_boundaries_work_with_narrow_trapping_context(self):
        for value in ('1e12', '-1e12', '1e-12', '-1e-12', '0'):
            record = fixture()
            record['quantities'][0]['value'] = value
            expected = prepare(record)
            self.assertEqual(expected['status'], 'PREPARED_SOURCE_ONLY')
            with self.subTest(value=value):
                with localcontext() as context:
                    context.prec = 6
                    context.Emax = 6
                    context.Emin = -6
                    for signal in (Overflow, Underflow, Inexact, Rounded):
                        context.traps[signal] = True
                    self.assertEqual(prepare(record), expected)
                    self.assertEqual(prepare(json.dumps(record)), expected)

    def test_review_preserves_wire_values_input_and_context_flags(self):
        record = fixture()
        record['quantities'][0]['value'] = '1.234567891234'
        record['quantities'][0]['uncertainty'] = '0.123456789123'
        original = copy.deepcopy(record)
        expected = prepare(record)
        with localcontext() as context:
            context.prec = 6
            context.clear_flags()
            flags_before = dict(context.flags)
            self.assertEqual(prepare(record), expected)
            self.assertEqual(dict(context.flags), flags_before)
        self.assertEqual(record, original)
        self.assertEqual(expected['candidate']['atlas_one']['packet']['measurements'],
                         original['quantities'])


if __name__ == '__main__':
    unittest.main()
