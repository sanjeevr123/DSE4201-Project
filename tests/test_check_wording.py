"""Tests for scripts/check_wording.py: banned phrases, conditional phrases and the per-paragraph marker."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_wording import check  # noqa: E402


def test_banned_phrase_is_found_case_insensitively():
    hits, _ = check("This shows No Effect at all.")
    assert [h[1] for h in hits] == ["No Effect"]


def test_conditional_phrase_needs_interval_in_same_paragraph():
    assert check("The models are indistinguishable.")[0]
    assert not check("The models are indistinguishable (95% CI [-0.01, 0.01]).")[0]
    assert check("The models are indistinguishable.\n\nThe 95% CI is wide.")[0]


def test_five_percent_level_must_say_which():
    assert check("Significant at the 5% level.")[0]
    assert not check("Significant at the one-sided 5% level.")[0]


def test_marker_skips_only_its_paragraph():
    hits, skipped = check("no effect wording-ok\n\nno effect")
    assert skipped == 1 and len(hits) == 1
