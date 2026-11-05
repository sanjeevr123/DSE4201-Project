# Result (holdout)

**Outcome: O2**

The hold-out data neither establish an improvement nor exclude one. The estimate is -0.0013 (95% CI [-0.0037, +0.0012]); an improvement of at least 0.0031 (the minimum detectable difference for the one-sided 5% test, 80% power) would have been detected with 80% probability, and smaller improvements, including none, are consistent with the data.

## Primary test: RSC_P_N vs CCC_S_N, tail level 5%, one-sided 5% test (preregistered)

Loss difference richer minus baseline; negative means the switching model is better.

| n | mean diff | HAC SE | 95% CI (two-sided) | t | p (one-sided) | p (two-sided) | lower 95% one-sided bound | MDE two-sided (2.8016 SE) | MDE one-sided (2.4865 SE) |
|---|---|---|---|---|---|---|---|---|---|
| 1508 | -0.00126 | 0.00126 | [-0.00374, +0.00121] | -1.002 | 0.1582 | 0.3165 | -0.00334 | 0.00353 | 0.00314 |

SESOI = 0.002; lower bound not above -0.002.
Simulated power at 1,508 days: 18.2% for the moderate and 35.2% for the strong simulated shift, one-sided 5% test, 1,508 days.

## Secondary (unadjusted, labelled secondary)

### calibration

| arm | alpha | n | hits | hit_rate | kupiec_lr | kupiec_p | independence_lr | independence_p | cc_lr | cc_p | z2 | z2_p_underestimated | z2_p_two_sided | z2_sim_mean | mean_es_exceedance_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RSC_P_N | 0.05 | 1508 | 104 | 0.068966 | 10.264 | 0.0013564 | 0.4997 | 0.47963 | 10.764 | 0.0045989 | 0.61568 | 0.00019996 | 0.00039992 | -4.8918e-05 | 1.1714 |
| CCC_S_N | 0.05 | 1508 | 103 | 0.068302 | 9.5911 | 0.0019553 | 0.58477 | 0.44445 | 10.176 | 0.0061709 | 0.6064 | 0.00019996 | 0.00039992 | 0.00010274 | 1.176 |
| RSC_P_N | 0.025 | 1508 | 66 | 0.043767 | 17.868 | 2.3683e-05 | 0.0044847 | 0.94661 | 17.872 | 0.00013157 | 1.0831 | 0.00019996 | 0.00039992 | 0.0030975 | 1.1899 |
| CCC_S_N | 0.025 | 1508 | 65 | 0.043103 | 16.725 | 4.3217e-05 | 0.01472 | 0.90343 | 16.739 | 0.00023179 | 1.0635 | 0.00019996 | 0.00039992 | -0.0018343 | 1.1968 |

### secondary_ladder

| step | richer | baseline | n | mean_diff | se | ci_lo | ci_hi | t | p_two_sided | mde_two_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| B vs A | B|pooled|N | A|pooled|N | 1508 | -0.09518 | 0.087898 | -0.26746 | 0.077101 | -1.0828 | 0.27888 | 0.24626 |
| D vs B | D|pooled|N | B|pooled|N | 1508 | 0.015503 | 0.011711 | -0.0074494 | 0.038456 | 1.3239 | 0.18554 | 0.032808 |
| CCC vs B | CCC_S_N | B|pooled|N | 1508 | -0.1107 | 0.082029 | -0.27147 | 0.05008 | -1.3495 | 0.17718 | 0.22981 |
| RSC vs D | RSC_S_N | D|pooled|N | 1508 | -0.12987 | 0.091867 | -0.30993 | 0.050193 | -1.4136 | 0.15747 | 0.25738 |
| RSC vs CCC | RSC_S_N | CCC_S_N | 1508 | -0.0036666 | 0.0032919 | -0.010119 | 0.0027855 | -1.1138 | 0.26535 | 0.0092225 |
| DCC vs RSC | DCC_N | RSC_S_N | 1508 | -0.0060486 | 0.014824 | -0.035104 | 0.023007 | -0.40802 | 0.68326 | 0.041531 |

### secondary_focus_year

| year | n | mean_diff | se | ci_lo | ci_hi | note |
|---|---|---|---|---|---|---|
| 2022 | 251 | -0.00094583 | 0.0040517 | -0.0088871 | 0.0069955 | interval only, not tested |

### secondary_gw_conditional

| n | gw_stat | df | gw_p | coef_const | coef_lagcorr | share_pos_corr | n_pos | mean_d_pos | mean_d_nonpos |
|---|---|---|---|---|---|---|---|---|---|
| 1508 | 1.3962 | 2 | 0.49753 | -0.0012127 | 0.0013649 | 0.44231 | 667 | -0.00041471 | -0.001937 |

### secondary_alpha_and_t_chain

| analysis | alpha | richer | baseline | n | mean_diff | se | ci_lo | ci_hi | t | p_two_sided | mde_two_sided |
|---|---|---|---|---|---|---|---|---|---|---|---|
| alpha 2.5%, Gaussian chain | 0.025 | RSC_P_N | CCC_S_N | 1508 | -0.0026446 | 0.002217 | -0.0069899 | 0.0017006 | -1.1929 | 0.2329 | 0.006211 |
| alpha 5%, Student-t chain | 0.05 | RSC_P_t | CCC_S_t | 1508 | -0.0011561 | 0.0012099 | -0.0035276 | 0.0012153 | -0.95554 | 0.3393 | 0.0033898 |
| alpha 2.5%, Student-t chain | 0.025 | RSC_P_t | CCC_S_t | 1508 | -0.0022991 | 0.0019757 | -0.0061715 | 0.0015734 | -1.1636 | 0.24457 | 0.0055353 |

### secondary_spa

| benchmark | n | reps | seed | p_consistent | p_upper | best_candidate | best_minus_benchmark |
|---|---|---|---|---|---|---|---|
| GARCHt | 1508 | 2000 | 0 | 0.477 | 0.477 | RSC | -0.044389 |

### diagnostics

```
{
  "psd_repairs": 0,
  "psd_matrices": 144,
  "margin_fallbacks": [],
  "dcc_refits": 24,
  "dcc_fallbacks": 0,
  "git_head": "c4495daa72ad3a16a01742932104404046406720",
  "freeze_tag": "b2cbbaace21c08a1a558023bafe9ba823cbec706",
  "raw_sha256": "0ab8c7f353a7223e154cc3ee4cc3656c465dded45c19269fc24efba371150e29",
  "runtime_s": 27.001487016677856,
  "python": "3.9.6"
}
```
