# Result (pseudo)

DRY RUN (2016-2019): a pipeline check; it enters no argument for the hypothesis.

**Outcome: O2**

The hold-out data neither establish an improvement nor exclude one. The estimate is -0.0020 (95% CI [-0.0049, +0.0009]); an improvement of at least 0.0036 (the minimum detectable difference for the one-sided 5% test, 80% power) would have been detected with 80% probability, and smaller improvements, including none, are consistent with the data.

## Primary test: RSC_P_N vs CCC_S_N, tail level 5%, one-sided 5% test (preregistered)

Loss difference richer minus baseline; negative means the switching model is better.

| n | mean diff | HAC SE | 95% CI (two-sided) | t | p (one-sided) | p (two-sided) | lower 95% one-sided bound | MDE two-sided (2.8016 SE) | MDE one-sided (2.4865 SE) |
|---|---|---|---|---|---|---|---|---|---|
| 1006 | -0.00199 | 0.00146 | [-0.00485, +0.00087] | -1.364 | 0.0863 | 0.1727 | -0.00439 | 0.00409 | 0.00363 |

SESOI = 0.002; lower bound not above -0.002.
Simulated power at 1,508 days: 18.2% for the moderate and 35.2% for the strong simulated shift, one-sided 5% test, 1,508 days.

## Secondary (unadjusted, labelled secondary)

### calibration

| arm | alpha | n | hits | hit_rate | kupiec_lr | kupiec_p | independence_lr | independence_p | cc_lr | cc_p | z2 | z2_p_underestimated | z2_p_two_sided | z2_sim_mean | mean_es_exceedance_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RSC_P_N | 0.05 | 1006 | 42 | 0.04175 | 1.5237 | 0.21706 | 0.41404 | 0.51992 | 1.9377 | 0.37951 | -0.10346 | 0.77365 | 0.45311 | 0.0017921 | 1.0737 |
| CCC_S_N | 0.05 | 1006 | 43 | 0.042744 | 1.1704 | 0.27932 | 0.49509 | 0.48166 | 1.6655 | 0.43486 | -0.082533 | 0.70866 | 0.58308 | 0.00083743 | 1.0732 |
| RSC_P_N | 0.025 | 1006 | 24 | 0.023857 | 0.054753 | 0.81499 | 0.27538 | 0.59975 | 0.33013 | 0.84784 | 0.01642 | 0.45811 | 0.91622 | 0.00083615 | 1.0651 |
| CCC_S_N | 0.025 | 1006 | 24 | 0.023857 | 0.054753 | 0.81499 | 0.27538 | 0.59975 | 0.33013 | 0.84784 | 0.022493 | 0.43751 | 0.87502 | -0.0042426 | 1.0715 |

### secondary_ladder

| step | richer | baseline | n | mean_diff | se | ci_lo | ci_hi | t | p_two_sided | mde_two_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| B vs A | B|pooled|N | A|pooled|N | 1006 | 0.0034739 | 0.017024 | -0.029894 | 0.036842 | 0.20405 | 0.83831 | 0.047695 |
| D vs B | D|pooled|N | B|pooled|N | 1006 | -0.0038558 | 0.0036192 | -0.010949 | 0.0032379 | -1.0654 | 0.28671 | 0.01014 |
| CCC vs B | CCC_S_N | B|pooled|N | 1006 | -0.031153 | 0.024628 | -0.079425 | 0.017118 | -1.2649 | 0.20589 | 0.068999 |
| RSC vs D | RSC_S_N | D|pooled|N | 1006 | -0.030517 | 0.024073 | -0.077701 | 0.016667 | -1.2677 | 0.20492 | 0.067444 |
| RSC vs CCC | RSC_S_N | CCC_S_N | 1006 | -0.0032193 | 0.003337 | -0.0097597 | 0.0033212 | -0.96472 | 0.33468 | 0.0093489 |
| DCC vs RSC | DCC_N | RSC_S_N | 1006 | -0.023615 | 0.0094767 | -0.042189 | -0.0050401 | -2.4918 | 0.012708 | 0.02655 |

### secondary_focus_year

| year | n | mean_diff | se | ci_lo | ci_hi | note |
|---|---|---|---|---|---|---|
| 2018 | 251 | -0.0032145 | 0.0040119 | -0.011078 | 0.0046489 | interval only, not tested |

### secondary_gw_conditional

| n | gw_stat | df | gw_p | coef_const | coef_lagcorr | share_pos_corr | n_pos | mean_d_pos | mean_d_nonpos |
|---|---|---|---|---|---|---|---|---|---|
| 1006 | 1.9209 | 2 | 0.38273 | -0.0033916 | -0.0035927 | 0.031809 | 32 | -0.0050293 | -0.0018913 |

### secondary_alpha_and_t_chain

| analysis | alpha | richer | baseline | n | mean_diff | se | ci_lo | ci_hi | t | p_two_sided | mde_two_sided |
|---|---|---|---|---|---|---|---|---|---|---|---|
| alpha 2.5%, Gaussian chain | 0.025 | RSC_P_N | CCC_S_N | 1006 | -0.0027783 | 0.0022009 | -0.007092 | 0.0015354 | -1.2624 | 0.20682 | 0.006166 |
| alpha 5%, Student-t chain | 0.05 | RSC_P_t | CCC_S_t | 1006 | -0.0015249 | 0.0014024 | -0.0042735 | 0.0012238 | -1.0874 | 0.27688 | 0.0039289 |
| alpha 2.5%, Student-t chain | 0.025 | RSC_P_t | CCC_S_t | 1006 | -0.0015689 | 0.0019316 | -0.0053548 | 0.0022171 | -0.81222 | 0.41667 | 0.0054116 |

### secondary_spa

| benchmark | n | reps | seed | p_consistent | p_upper | best_candidate | best_minus_benchmark |
|---|---|---|---|---|---|---|---|
| GARCHt | 1006 | 2000 | 0 | 0.9425 | 0.9425 | RSC | 0.023354 |

### diagnostics

```
{
  "psd_repairs": 0,
  "psd_matrices": 96,
  "margin_fallbacks": [],
  "dcc_refits": 16,
  "dcc_fallbacks": 0,
  "git_head": "694639cc66e1aca027e8a85ad0554f98eb03a286",
  "freeze_tag": null,
  "raw_sha256": "0ab8c7f353a7223e154cc3ee4cc3656c465dded45c19269fc24efba371150e29",
  "runtime_s": 17.55703902244568,
  "python": "3.9.6"
}
```
