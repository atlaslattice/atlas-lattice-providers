"""Public/synthetic-only review text tests; no private sources or host calls."""
import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from labs.atlas_labs_v32 import _text, prepare


class ReviewTextBoundaryTests(unittest.TestCase):
    def test_bidi_override(self):
        self.assertFalse(_text("Hypothesis\u202e123"))

    def test_bidi_isolate(self):
        self.assertFalse(_text("Hypothesis\u2066abc"))

    def test_lrm(self):
        self.assertFalse(_text("Hypothesis\u200eabc"))

    def test_rtl_mark(self):
        self.assertFalse(_text("Hypothesis\u200fabc"))

    def test_arabic_letter_mark(self):
        self.assertFalse(_text("Hypothesis\u061cabc"))

    def test_unicode_line_separator(self):
        self.assertFalse(_text("Hypothesis\u2028abc"))

    def test_paragraph_separator(self):
        self.assertFalse(_text("Hypothesis\u2029abc"))

    def test_delete(self):
        self.assertFalse(_text("Hypothesis\x7fabc"))

    def test_c1_control(self):
        self.assertFalse(_text("Hypothesis\x85abc"))

    def test_bom(self):
        self.assertFalse(_text("Hypothesis\ufeffabc"))

    def test_legitimate_greek_text(self):
        self.assertTrue(_text("α + β → γ; uncertainty 5 μm"))

    def test_normal_ascii(self):
        self.assertTrue(_text("Model revision v1.2 (design only)"))

    def test_multilingual_text(self):
        self.assertTrue(_text("宇宙物理研究 · 量子效应"))

    def test_existing_newline_rejected(self):
        self.assertFalse(_text("line\nline"))

    def test_existing_blank_rejected(self):
        self.assertFalse(_text("   "))

    def test_no_custom_str_subclass(self):
        class E(str):
            pass
        self.assertFalse(_text(E("Hello")))

    def test_hidden_format_controls_are_not_review_text(self):
        # All are non-printing; accepting them would permit visually
        # indistinguishable but byte-distinct synthetic review statements.
        for cp in (0x00AD, 0x034F, 0x180E, 0x200B,
                   0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0x206A):
            with self.subTest(codepoint=f"U+{cp:04X}"):
                self.assertFalse(_text("Public" + chr(cp) + " review"))

    def test_multilingual_joiners_are_preserved(self):
        # Joiners are meaningful in real writing; reject only selected
        # invisible review-format controls, not all non-ASCII text.
        for example in ("Hello 👩‍🔬", "فارسی‌نویسی", "α + β → γ"):
            with self.subTest(example=example):
                self.assertTrue(_text(example))

    def test_prepare_holds_hidden_format_in_each_review_field(self):
        base = json.loads((ROOT / "examples/atlas_labs_v32_synthetic.json").read_text(encoding="utf-8"))
        for field in ("title", "hypothesis", "falsifier", "model_revision"):
            for cp in (0x00AD, 0x034F, 0x200B, 0x2060, 0x2063):
                with self.subTest(field=field, codepoint=f"U+{cp:04X}"):
                    record = copy.deepcopy(base)
                    record[field] = "Public" + chr(cp) + " review"
                    self.assertEqual(prepare(record), {
                        "status": "HOLD", "reason": "INVALID_OR_UNAUTHORIZED_PUBLIC_SOURCE",
                        "source_count": 0, "candidate": None})

    def test_prepare_denies_spoof_text_without_echoing(self):
        # Integration case: requires the checked-out source and public fixture.
        base = json.loads(
            (ROOT / "examples/atlas_labs_v32_synthetic.json").read_text(encoding="utf-8")
        )
        expected = {
            "status": "HOLD",
            "reason": "INVALID_OR_UNAUTHORIZED_PUBLIC_SOURCE",
            "source_count": 0,
            "candidate": None,
        }
        for field in ("title", "hypothesis", "falsifier", "model_revision"):
            for token in ("\u202e", "\u2066", "\u2028", "\x7f"):
                with self.subTest(field=field, token=repr(token)):
                    x = copy.deepcopy(base)
                    x[field] = "Synthetic " + token + " review"
                    result = prepare(x)
                    self.assertEqual(result, expected)
                    self.assertNotIn("Synthetic ", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
