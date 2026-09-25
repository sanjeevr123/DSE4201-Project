"""Smoke test for src.engine.christoffersen_ind (promoted from
starter/pilot_real_data.py). Not itemized explicitly in WP1's bullet list,
but Christoffersen independence is named under the pilot's scoring tools and
its correctness supports the G1 pipeline-correctness go/no-go criterion."""
from __future__ import annotations

import numpy as np

from src.engine import christoffersen_ind


def test_iid_hits_give_high_pvalue():
    rng = np.random.default_rng(0)
    hits = (rng.random(5000) < 0.05).astype(int)
    p = christoffersen_ind(hits)
    assert p > 0.05


def test_clustered_hits_give_low_pvalue():
    # Force exceptions to cluster: long runs of 1s and 0s, alternating,
    # which strongly violates independence (P(hit|hit) >> P(hit|no hit)).
    block = np.array([1] * 20 + [0] * 200)
    hits = np.tile(block, 20)
    p = christoffersen_ind(hits)
    assert p < 0.01
