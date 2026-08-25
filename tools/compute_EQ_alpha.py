import pandas as pd
import numpy as np
import sys
import os
import argparse

# ====================================================================
# CONSTANTS (override individual ones via CLI where a flag exists;
# edit here for anything without a flag)
# ====================================================================

LONG_CYCLE = 385
SHORT_CYCLE = 23
DATA_SLICE = 3 * LONG_CYCLE          # training window length, in trading days

SHORT_MIN, SHORT_MAX = 17, 54        # plastic short-lag range
LONG_MIN, LONG_MAX = 219, 676        # plastic long-lag range

N_YEARS = 25                         # how far back we're willing to look
TRADING_DAYS_PER_YEAR = 252
NUM_SLICES = 20                      # evenly-spaced windows, aggregated

ALPHA_MIN, ALPHA_MAX, ALPHA_STEP = 0.01, 0.99, 0.01

RHO = 1.3247179572447460
PCU = RHO - 1                        # correction relative to resolved state, ~0.324718
PCU_RHO = PCU / RHO                  # correction relative to peak,           ~0.245122

CLOSE_COL = 'close'
DATE_COL = 'Date'

# ====================================================================
# RSS COMPUTATION
# ====================================================================

def slice_rss_by_alpha(Y, slice_start, data_slice, short_cycle, long_cycle, alphas):
    """
    For one DATA_SLICE-length window starting at slice_start, and for each
    alpha, build E = alpha*Y_(t-short) + (1-alpha)*Y_(t-long), regress
    Y_current ~ m*E + b (OLS, single predictor + intercept), and return the
    residual sum of squares. Vectorized across the whole alpha grid at once.

    Requires slice_start - long_cycle >= 0 in the caller's coordinate space.
    """
    idx_current = slice(slice_start, slice_start + data_slice)
    idx_short = slice(slice_start - short_cycle, slice_start + data_slice - short_cycle)
    idx_long = slice(slice_start - long_cycle, slice_start + data_slice - long_cycle)

    Y_current = Y[idx_current]
    Y_short = Y[idx_short]
    Y_long = Y[idx_long]

    a = alphas[:, None]                              # (n_alpha, 1)
    E = a * Y_short[None, :] + (1 - a) * Y_long[None, :]   # (n_alpha, data_slice)  == X in LINEST(Y, X)

    # OLS single-predictor regression per alpha: Y_current ~ m*E + b,
    # then SSresid, matching Excel LINEST(Y_current, E, TRUE, TRUE) row 5 col 2.
    mean_Y = Y_current.mean()
    mean_E = E.mean(axis=1)                                        # (n_alpha,)
    dY = Y_current[None, :] - mean_Y                                # (1, data_slice)
    dE = E - mean_E[:, None]                                        # (n_alpha, data_slice)

    cov_EY = np.sum(dE * dY, axis=1)                                # (n_alpha,)
    var_E = np.sum(dE ** 2, axis=1)                                 # (n_alpha,)

    slope = np.where(var_E > 0, cov_EY / var_E, 0.0)
    intercept = mean_Y - slope * mean_E

    pred = slope[:, None] * E + intercept[:, None]
    resid = Y_current[None, :] - pred
    return np.sum(resid ** 2, axis=1)                               # (n_alpha,) == SSresid per alpha


def find_crossing(alphas, ratio, target):
    """
    Linear-interpolated alpha where ratio(alpha) crosses target,
    scanning from the smallest alpha upward (ratio is expected to
    decrease as alpha increases toward the plastic knee).
    Returns None if the target is never reached.
    """
    below = np.where(ratio <= target)[0]
    if len(below) == 0:
        return None
    i = below[0]
    if i == 0:
        return alphas[0]
    r1, r2 = ratio[i - 1], ratio[i]
    a1, a2 = alphas[i - 1], alphas[i]
    return a1 + (target - r1) / (r2 - r1) * (a2 - a1)


# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect the PCU / PCU-over-rho plastic knee (alpha) from historical price data")
    parser.add_argument("-f", "--filename", required=True, help="Filename of the historical CSV data file")
    parser.add_argument("-l", "--lags", help="Override as short,long (e.g. 23,416)")
    parser.add_argument("-d", "--data_slice", type=int, help="Override DATA_SLICE (days per training window, default = 3 x long-lag)")

    args = parser.parse_args()

    # --- resolve short/long cycle ---
    short_cycle, long_cycle = SHORT_CYCLE, LONG_CYCLE
    if args.lags:
        parts = args.lags.split(',')
        if len(parts) != 2:
            print("Error: -l must be short,long (e.g. 23,416)")
            sys.exit(1)
        short_cycle, long_cycle = int(parts[0]), int(parts[1])
        if not (SHORT_MIN <= short_cycle <= SHORT_MAX):
            print(f"Error: short lag {short_cycle} outside plastic range [{SHORT_MIN},{SHORT_MAX}]")
            sys.exit(1)
        if not (LONG_MIN <= long_cycle <= LONG_MAX):
            print(f"Error: long lag {long_cycle} outside plastic range [{LONG_MIN},{LONG_MAX}]")
            sys.exit(1)

    # --- resolve data slice (bounds depend on the resolved long_cycle above) ---
    data_slice = args.data_slice if args.data_slice is not None else 3 * long_cycle
    if not (long_cycle < data_slice < 4 * long_cycle):
        print(f"Error: DATA_SLICE={data_slice} must satisfy LONG_CYCLE({long_cycle}) < DATA_SLICE < 4*LONG_CYCLE({4*long_cycle})")
        sys.exit(1)

    # --- load data ---
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

    print(f"Loaded {args.filename}: {n_total} observations, {data[DATE_COL].min().date()} to {data[DATE_COL].max().date()}")

    # --- restrict to last N_YEARS (or all available data, whichever is smaller) ---
    cutoff_date = data[DATE_COL].max() - pd.DateOffset(years=N_YEARS)
    earliest_usable_idx = int(np.searchsorted(dates, np.datetime64(cutoff_date)))

    # the LONG_CYCLE lookback must also stay within the N_YEARS boundary,
    # so the first valid "current" index is pushed forward by long_cycle
    usable_start = earliest_usable_idx + long_cycle
    usable_end = n_total - 1  # last available index

    usable_len = usable_end - usable_start + 1
    if usable_len < data_slice:
        print(f"Error: not enough history within the last {N_YEARS} years for one DATA_SLICE window "
              f"(need {data_slice} usable days, have {usable_len}).")
        sys.exit(1)

    # --- 20 evenly-spaced slice start positions across the usable range ---
    last_possible_start = usable_end - data_slice + 1
    if last_possible_start <= usable_start:
        slice_starts = [usable_start]
    else:
        slice_starts = np.linspace(usable_start, last_possible_start, NUM_SLICES).astype(int)
        slice_starts = sorted(set(slice_starts.tolist()))

    print(f"Configuration: short={short_cycle}  long={long_cycle}  data_slice={data_slice}  "
          f"n_years={N_YEARS}  slices_used={len(slice_starts)} (requested {NUM_SLICES})")
    print(f"Restricted range: {data[DATE_COL].iloc[earliest_usable_idx].date()} onward "
          f"(no lookups before this date, including LONG_CYCLE lags)")

    # --- aggregate RSS(alpha) across all slices ---
    alphas = np.round(np.arange(ALPHA_MIN, ALPHA_MAX + 1e-9, ALPHA_STEP), 2)
    rss_agg = np.zeros_like(alphas)

    for s in slice_starts:
        rss_agg += slice_rss_by_alpha(Y, s, data_slice, short_cycle, long_cycle, alphas)

    # --- locate PCU and PCU/rho crossings ---
    R0 = rss_agg[0]
    ratio = rss_agg / R0

    alpha_pcu = find_crossing(alphas, ratio, PCU)
    alpha_pcu_rho = find_crossing(alphas, ratio, PCU_RHO)

    print()
    print(f"RSS(alpha={alphas[0]:.2f}) [reference] = {R0:,.2f}")
    print(f"PCU        = {PCU:.6f}   -> plastic knee alpha = {alpha_pcu:.3f}" if alpha_pcu is not None
          else f"PCU        = {PCU:.6f}   -> not reached in alpha range")
    print(f"PCU/rho    = {PCU_RHO:.6f}   -> plastic knee alpha = {alpha_pcu_rho:.3f}" if alpha_pcu_rho is not None
          else f"PCU/rho    = {PCU_RHO:.6f}   -> not reached in alpha range")