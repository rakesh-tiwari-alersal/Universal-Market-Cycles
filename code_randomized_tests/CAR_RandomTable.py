"""
CAR_RandomTable.py

Tests cycle SPECIFICITY (as opposed to detector validity, which the
GBM-null test already covers): does the plastic 39-cycle table's real-data
CAR reflect something special about those particular values, or would any
comparably-structured 39-cycle candidate set do about as well on the same
real data?

Design (2x2, complementary to CAR_RandomData.py):
                        Table3 (plastic)         Random 39-cycle tables
  Real market data      68% (given/recomputed)   <- THIS SCRIPT builds this distribution
  Synthetic GBM noise   57% mean, 3.2 sigma       (already covered by CAR_RandomData.py)
                        (already done)

Key efficiency point: a real instrument's DETECTED periods (raw Cycle1/
Cycle2 from your existing match_psd_results_{ac}.csv files) do not depend
on which candidate table you compare them against -- only the matching
step does. So this script does NOT re-run any periodogram computation. It
reads your existing real per-instrument detection output, and for Table3
plus N randomly-generated alternative tables, re-runs ONLY the
nearest-neighbor matching + CAR calculation against each candidate table,
using the exact same tolerance-based "covered" definition CAR.py uses.

Random tables are constrained to match Table 3's own structural
properties exactly:
  - 39 unique integers
  - drawn from [215, 680] (same MIN_PERIOD/MAX_PERIOD as the real pipeline)
  - minimum gap between consecutive (sorted) values >= 5 days, matching
    Table 3's own tightest neighbor spacing (403/408) -- this guarantees
    no table's own +-1 tolerance windows overlap between neighbors,
    exactly as is true of Table 3.

Usage:
  python CAR_RandomTable.py [--n-tables 200] [--tolerance 1]
                                       [--method psd] [--results-dir psd_results]
                                       [--seed 42]

Reads: <results-dir>/match_<method>_results_{eq,ix,cr,co,fx}.csv
       (the same real result files CAR.py reads -- place your real files
       there before running this)
"""

import argparse
import csv
import os
import sys
import numpy as np
import pandas as pd

TABLE_CYCLES = [
    219, 237, 243, 250, 259, 267, 273,
    290, 308, 314, 322, 332, 344, 354,
    362, 368, 385, 403, 408, 416, 426,
    440, 456, 469, 479, 487, 493, 510,
    528, 534, 541, 551, 565, 622, 635,
    645, 653, 659, 676
]

MIN_PERIOD = 215
MAX_PERIOD = 680
ASSET_CLASSES = ['eq', 'ix', 'cr', 'co', 'fx']


def min_gap(table):
    s = sorted(table)
    return min(b - a for a, b in zip(s, s[1:]))


def find_closest_cycle(period, cycle_table):
    """Same logic as CAR.py's find_closest_cycle."""
    if period is None or (isinstance(period, float) and np.isnan(period)) or period == '':
        return None, None
    try:
        period_int = int(period)
        closest = min(cycle_table, key=lambda x: abs(x - period_int))
        return closest, abs(period_int - closest)
    except (ValueError, TypeError):
        return None, None


def generate_random_table(n_cycles, min_period, max_period, min_gap_required, rng):
    """
    Exact, uniform sampling of an n_cycles-subset of [min_period, max_period]
    with all consecutive gaps >= min_gap_required.

    Naive rejection sampling (draw n random points, check gaps, retry) is
    NOT used here because it is essentially infeasible for this constraint:
    a uniformly random 39-point subset of a 466-day range almost always has
    at least one close pair by pure birthday-paradox clustering, so the
    acceptance rate of blind rejection sampling is astronomically low.

    Instead this uses the standard bijection for gap-constrained ordered
    selection: sorted x_1<...<x_n with x_(i+1)-x_i >= g is equivalent to
    an ordinary (no-gap) selection of n distinct points y_1<...<y_n in a
    REDUCED range, via y_i = x_i - (i-1)*(g-1). This is always feasible
    whenever (n-1)*(g-1) <= (max_period-min_period), samples uniformly at
    random over the full valid combinatorial space, and needs no retries.
    """
    reduced_max = max_period - (n_cycles - 1) * (min_gap_required - 1)
    if reduced_max < min_period:
        raise ValueError(
            f"Infeasible constraints: {n_cycles} cycles with min_gap={min_gap_required} "
            f"cannot fit in [{min_period},{max_period}]."
        )
    y = rng.choice(np.arange(min_period, reduced_max + 1), size=n_cycles, replace=False)
    y.sort()
    x = y + np.arange(n_cycles) * (min_gap_required - 1)
    return x.tolist()


def load_real_raw_periods(results_dir, method):
    """
    Load real per-instrument raw detected periods (Cycle1/Cycle2), independent
    of any candidate table. This is the SAME data CAR.py's load_results reads --
    we just use the raw period columns instead of the precomputed Match/Delta
    columns, since we're re-matching against different candidate tables.
    """
    frames = []
    for ac in ASSET_CLASSES:
        path = os.path.join(results_dir, f"match_{method}_results_{ac}.csv")
        if os.path.exists(path):
            frames.append(pd.read_csv(path))
    if not frames:
        print(f"ERROR: no real result files found in {results_dir}/match_{method}_results_{{"
              f"{','.join(ASSET_CLASSES)}}}.csv")
        print("Place your real per-instrument detection output there first (the same files")
        print("CAR.py reads) -- this script does not re-run any detection, only re-matching.")
        sys.exit(1)
    df = pd.concat(frames, ignore_index=True)
    if 'Cycle1' not in df.columns:
        print("ERROR: expected a 'Cycle1' column (raw detected period) in the result files.")
        sys.exit(1)
    return df


def car_for_table(raw_df, candidate_table, tolerance):
    """
    Re-match each instrument's raw detected period(s) against candidate_table
    and compute CAR, mirroring CAR.py's calculate_car 'covered' definition:
    an instrument counts as covered if EITHER detected cycle is within
    tolerance of some value in candidate_table. Instruments with no detected
    cycle at all (both Cycle1 and Cycle2 blank/NaN) are excluded from the
    denominator, same as CAR.py's dropna behavior.
    """
    covered = 0
    processed = 0
    for _, row in raw_df.iterrows():
        c1 = row.get('Cycle1', None)
        c2 = row.get('Cycle2', None) if 'Cycle2' in raw_df.columns else None

        _, d1 = find_closest_cycle(c1, candidate_table)
        _, d2 = find_closest_cycle(c2, candidate_table)

        if d1 is None and d2 is None:
            continue  # no cycle detected at all -- excluded, same as CAR.py

        processed += 1
        hit = (d1 is not None and d1 <= tolerance) or (d2 is not None and d2 <= tolerance)
        if hit:
            covered += 1

    car = covered / processed if processed > 0 else float('nan')
    return car, covered, processed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-tables", type=int, default=200)
    parser.add_argument("--tolerance", type=int, default=1, choices=[1, 2, 3])
    parser.add_argument("--method", default="psd")
    parser.add_argument("--results-dir", default="psd_results")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-csv", default="random_table_test_results.csv")
    args = parser.parse_args()

    table3_min_gap = min_gap(TABLE_CYCLES)
    print(f"Table 3: {len(TABLE_CYCLES)} cycles, range [{min(TABLE_CYCLES)},{max(TABLE_CYCLES)}], "
          f"min gap={table3_min_gap} days")
    print(f"Random tables will match: 39 cycles, range [{MIN_PERIOD},{MAX_PERIOD}], "
          f"min gap>={table3_min_gap} days\n")

    raw_df = load_real_raw_periods(args.results_dir, args.method)
    print(f"Loaded {len(raw_df)} real instrument detection rows from {args.results_dir}/\n")

    # Recompute Table 3's own CAR via the IDENTICAL code path as the random
    # tables (not trusted from the paper/CAR.py output) -- guarantees a
    # perfectly apples-to-apples comparison with zero methodology drift.
    car3, covered3, processed3 = car_for_table(raw_df, TABLE_CYCLES, args.tolerance)
    print(f"Table 3 (plastic cycles) CAR at tolerance +-{args.tolerance}: "
          f"{car3*100:.2f}%  ({covered3}/{processed3})\n")

    rng = np.random.default_rng(args.seed)
    print(f"Generating and testing {args.n_tables} random structurally-matched tables...")
    random_cars = []
    with open(args.out_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['table_index', 'car_pct', 'covered', 'processed'])
        for i in range(args.n_tables):
            table = generate_random_table(39, MIN_PERIOD, MAX_PERIOD, table3_min_gap, rng)
            car, covered, processed = car_for_table(raw_df, table, args.tolerance)
            random_cars.append(car)
            writer.writerow([i, car * 100, covered, processed])
            if (i + 1) % 50 == 0 or i == args.n_tables - 1:
                print(f"  {i+1}/{args.n_tables} random tables tested")

    random_cars = np.array(random_cars)
    mean, std = random_cars.mean(), random_cars.std()
    n_ge = int((random_cars >= car3).sum())

    print("\n" + "=" * 72)
    print(f"CYCLE SPECIFICITY TEST -- tolerance +-{args.tolerance}, {args.n_tables} random tables")
    print("=" * 72)
    print(f"Table 3 (plastic) CAR:      {car3*100:.2f}%")
    print(f"Random tables CAR:          mean={mean*100:.2f}%  std={std*100:.2f}%  "
          f"range=[{random_cars.min()*100:.2f}%, {random_cars.max()*100:.2f}%]  (n={args.n_tables})")
    if std > 0:
        z = (car3 - mean) / std
        print(f"Table 3 is {z:.2f} standard deviations above the random-table mean")
    print(f"Random tables reaching or exceeding Table 3's CAR: {n_ge}/{args.n_tables}"
          f"  (empirical p <= {max(n_ge,1)/args.n_tables:.4f}{' (upper bound, 0 observed)' if n_ge==0 else ''})")
    print("=" * 72)
    print(f"\nPer-table results written to {args.out_csv}")


if __name__ == "__main__":
    main()