"""
compute_EQ_alpha.py

Single-purpose EQ alpha* estimator:
  - grid (min-max) normalized RSS(alpha) curve only -- no ratio-to-baseline method
  - single target: post-peak crossing of |dy/dalpha| = 1 - λ
  - alpha swept 0.00 -> 1.00 (all-trend -> all-correction)
  - 26-year lookback, 20 aggregated windows (cutoff lands ~Aug 2000)

Usage:
  python compute_EQ_alpha.py -f GSPC.csv -l 23,528 -d 1346
  python compute_EQ_alpha.py -f GSPC.csv -l 23,528 -d 1346 --verbose
"""

import pandas as pd
import numpy as np
import sys
import os
import argparse

SHORT_MIN, SHORT_MAX = 17, 54
LONG_MIN, LONG_MAX = 219, 676

N_YEARS = 26
NUM_SLICES = 20

ALPHA_MIN, ALPHA_MAX, ALPHA_STEP = 0.00, 1.00, 0.01

RHO = 1.32471795
LAMBDA = 1 - (1 / RHO)      # ~PCU/ρ numerically, equation (3) in the paper -- 0.245122
TARGET = 1 - LAMBDA         # 1/ρ numerically, 0.754878 -- but stated
                            

CLOSE_COL = 'close'
DATE_COL = 'Date'


def slice_rss_by_alpha(Y, slice_start, data_slice, short_cycle, long_cycle, alphas):
    idx_current = slice(slice_start, slice_start + data_slice)
    idx_short = slice(slice_start - short_cycle, slice_start + data_slice - short_cycle)
    idx_long = slice(slice_start - long_cycle, slice_start + data_slice - long_cycle)

    Y_current = Y[idx_current]
    Y_short = Y[idx_short]
    Y_long = Y[idx_long]

    a = alphas[:, None]
    E = a * Y_short[None, :] + (1 - a) * Y_long[None, :]

    mean_Y = Y_current.mean()
    mean_E = E.mean(axis=1)
    dY = Y_current[None, :] - mean_Y
    dE = E - mean_E[:, None]

    cov_EY = np.sum(dE * dY, axis=1)
    var_E = np.sum(dE ** 2, axis=1)

    slope = np.where(var_E > 0, cov_EY / var_E, 0.0)
    intercept = mean_Y - slope * mean_E

    pred = slope[:, None] * E + intercept[:, None]
    resid = Y_current[None, :] - pred
    return np.sum(resid ** 2, axis=1)


def find_post_peak_1_over_rho(alphas, dy_dx):
    """
    peak_idx: location of steepest descent (max |dy/dalpha|) -- purely a
    property of the curve, no target involved.
    Then searches for |dy/dalpha| = TARGET (= 1 - λ = 1/ρ) among
    crossings strictly after that peak.
    Returns (alpha_peak, alpha_star or None, all_post_peak_crossings).
    """
    peak_idx = int(np.argmax(np.abs(dy_dx)))
    alpha_peak = alphas[peak_idx]

    diffs = np.abs(dy_dx) - TARGET
    sign_changes = np.where(np.diff(np.sign(diffs)) != 0)[0]
    crossings = []
    for i in sign_changes:
        x1, x2 = alphas[i], alphas[i + 1]
        y1, y2 = diffs[i], diffs[i + 1]
        if y2 == y1:
            continue
        frac = -y1 / (y2 - y1)
        crossings.append(x1 + frac * (x2 - x1))

    post_peak = [c for c in crossings if c > alpha_peak]
    alpha_star = post_peak[0] if post_peak else None
    return alpha_peak, alpha_star, post_peak


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filename", required=True)
    parser.add_argument("-l", "--lags", required=True, help="short,long")
    parser.add_argument("-d", "--data_slice", type=int, help="Override data_slice (days per training window, default = 3 x long-lag)")
    parser.add_argument("--verbose", action="store_true", help="show peak location and full crossing list")
    args = parser.parse_args()

    short_cycle, long_cycle = (int(x) for x in args.lags.split(','))
    if not (SHORT_MIN <= short_cycle <= SHORT_MAX):
        print(f"Error: short lag {short_cycle} outside plastic range [{SHORT_MIN},{SHORT_MAX}]")
        sys.exit(1)
    if not (LONG_MIN <= long_cycle <= LONG_MAX):
        print(f"Error: long lag {long_cycle} outside plastic range [{LONG_MIN},{LONG_MAX}]")
        sys.exit(1)

    data_slice = args.data_slice if args.data_slice is not None else 3 * long_cycle
    if not (long_cycle < data_slice <= 5 * long_cycle):
        print(f"Error: data_slice={data_slice} must satisfy long_cycle({long_cycle}) < data_slice <= 5*long_cycle({5*long_cycle})")
        sys.exit(1)

    DATA_FILE_PATH = os.path.join('historical_data', args.filename)
    if not os.path.exists(DATA_FILE_PATH):
        print(f"Error: input file not found: {DATA_FILE_PATH}")
        sys.exit(1)

    data = pd.read_csv(DATA_FILE_PATH)
    data = data[data[CLOSE_COL] > 0].copy()
    data[DATE_COL] = pd.to_datetime(data[DATE_COL])
    data = data.sort_values(DATE_COL).reset_index(drop=True)

    Y = data[CLOSE_COL].values
    dates = data[DATE_COL].values
    n_total = len(Y)

    cutoff_date = data[DATE_COL].max() - pd.DateOffset(years=N_YEARS)
    earliest_usable_idx = int(np.searchsorted(dates, np.datetime64(cutoff_date)))
    usable_start = earliest_usable_idx + long_cycle
    usable_end = n_total - 1

    usable_len = usable_end - usable_start + 1
    if usable_len < data_slice:
        print(f"Error: not enough history within the last {N_YEARS} years for one window "
              f"(need {data_slice} usable days, have {usable_len}).")
        sys.exit(1)

    last_possible_start = usable_end - data_slice + 1
    if last_possible_start <= usable_start:
        slice_starts = [usable_start]
    else:
        slice_starts = np.linspace(usable_start, last_possible_start, NUM_SLICES).astype(int)
        slice_starts = sorted(set(slice_starts.tolist()))

    alphas = np.round(np.arange(ALPHA_MIN, ALPHA_MAX + 1e-9, ALPHA_STEP), 2)
    rss_agg = np.zeros_like(alphas)
    for s in slice_starts:
        rss_agg += slice_rss_by_alpha(Y, s, data_slice, short_cycle, long_cycle, alphas)

    y_grid = (rss_agg - rss_agg.min()) / (rss_agg.max() - rss_agg.min())
    dy_grid = np.gradient(y_grid, alphas)

    alpha_peak, alpha_star, post_peak = find_post_peak_1_over_rho(alphas, dy_grid)

    print(f"{args.filename}  short={short_cycle} long={long_cycle} data_slice={data_slice}  "
          f"({N_YEARS}yr history, {len(slice_starts)} windows)")

    if args.verbose:
        print(f"  dy/dalpha range: [{dy_grid.min():.4f}, {dy_grid.max():.4f}]")
        print(f"  alpha at steepest descent = {alpha_peak:.3f}")
        if len(post_peak) > 1:
            print(f"  (multiple post-peak crossings found: "
                  f"{', '.join(f'{c:.3f}' for c in post_peak)} -- using first)")

    if alpha_star is not None:
        print(f"alpha* @(1 - λ)= {alpha_star:.3f}")
    else:
        print("alpha* = not found (no post-peak crossing of 1 - λ (= 1/ρ) in range)")
