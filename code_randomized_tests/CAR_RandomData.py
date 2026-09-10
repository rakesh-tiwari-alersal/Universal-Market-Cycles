"""
CAR_RandomData.py

Automates the Monte Carlo null-model comparison against the REAL, UNMODIFIED
CAR.py. This script never edits, imports, or monkeypatches CAR.py -- it only
(1) temporarily swaps the input CSV files CAR.py reads, (2) invokes
`python CAR.py <method> -t <tolerance>` as a separate subprocess, exactly as
you would from the command line, and (3) parses CAR.py's own printed stdout.
CAR.py's code and logic are never touched.

Tolerance +-1 only: the thesis's claim is anchored on tolerance 1 (the other
tolerances exist only as supplementary context, not as claims this test is
meant to validate), so this script computes and reports tolerance 1 only.

What it does, per panel (default 50, produced earlier by compute_null_psd.py):
  1. Backs up your real psd_results/match_psd_results_{ac}.csv files (once,
     at the start) into psd_results/_real_backup/.
  2. Computes the REAL CAR number first (from the backed-up real files), via
     the same subprocess-call-to-CAR.py path, so the "real" number you're
     comparing against came from the identical code path as the null
     numbers -- not from a separately-remembered figure.
  3. For each of the null panels: copies that panel's 5 asset-class files
     (eq/ix/cr/co/fx) over match_psd_results_{ac}.csv, runs CAR.py, parses
     the printed CAR/z/p values.
  4. Restores your real files from backup at the end (and also on any
     crash, via try/finally) so psd_results/ is left exactly as it started.
  5. Prints and saves a summary: null CAR distribution (mean/std/min/max),
     and where the real CAR sits relative to that distribution (a Monte
     Carlo z-score, not just the analytic one CAR.py itself reports).

Usage:
  python CAR_RandomData.py [--n-panels 50] [--tolerance 1]
                            [--car-script CAR.py] [--results-dir psd_results]

Run this from the same working directory you'd normally run CAR.py from
(the one containing psd_results/ and CAR.py itself).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import csv

ASSET_CLASSES = ['eq', 'ix', 'cr', 'co', 'fx']

STDOUT_PATTERNS = {
    'processed': re.compile(r"Instruments with cycles detected:\s*(\d+)"),
    'car_covered': re.compile(r"CAR:\s*([\d.]+)%\s*\((\d+)\s*instruments\)"),
    'expected_random': re.compile(r"Expected random coverage:\s*([\d.]+)\s*instruments"),
    'excess': re.compile(r"Excess coverage:\s*(-?[\d.]+)%"),
    'zp': re.compile(r"z=(-?[\d.]+),\s*p=([\d.eE+-]+)"),
    'error': re.compile(r"^Error processing"),
}


def parse_car_stdout(stdout_text):
    """Parse CAR.py's own printed output. Returns a dict, or None on error/failure."""
    if STDOUT_PATTERNS['error'].search(stdout_text):
        return None

    m_proc = STDOUT_PATTERNS['processed'].search(stdout_text)
    m_car = STDOUT_PATTERNS['car_covered'].search(stdout_text)
    m_exp = STDOUT_PATTERNS['expected_random'].search(stdout_text)
    m_exc = STDOUT_PATTERNS['excess'].search(stdout_text)
    m_zp = STDOUT_PATTERNS['zp'].search(stdout_text)

    if not (m_proc and m_car and m_exp and m_exc and m_zp):
        return None

    return dict(
        processed=int(m_proc.group(1)),
        car_pct=float(m_car.group(1)),
        covered=int(m_car.group(2)),
        expected_random=float(m_exp.group(1)),
        excess_pct=float(m_exc.group(1)),
        z=float(m_zp.group(1)),
        p=float(m_zp.group(2)),
    )


def run_car(car_script, method, tolerance):
    """Invoke CAR.py as an unmodified subprocess and return parsed stdout, or None."""
    result = subprocess.run(
        [sys.executable, car_script, method, "-t", str(tolerance)],
        capture_output=True, text=True
    )
    parsed = parse_car_stdout(result.stdout)
    if parsed is None:
        print(f"    [warn] could not parse CAR.py output at tolerance={tolerance}:")
        print(f"           stdout: {result.stdout.strip()}")
        if result.stderr.strip():
            print(f"           stderr: {result.stderr.strip()}")
    return parsed


def backup_real_files(results_dir, method, backup_dir):
    if os.path.isdir(backup_dir): return []
    os.makedirs(backup_dir)
    backed_up = []
    for ac in ASSET_CLASSES:
        path = os.path.join(results_dir, f"match_{method}_results_{ac}.csv")
        if os.path.exists(path):
            shutil.copy2(path, os.path.join(backup_dir, os.path.basename(path)))
            backed_up.append(path)
    print(f"Backed up {len(backed_up)}/{len(ASSET_CLASSES)} real result files to {backup_dir}")
    return backed_up


def restore_real_files(results_dir, method, backup_dir):
    restored = 0
    for ac in ASSET_CLASSES:
        fname = f"match_{method}_results_{ac}.csv"
        src = os.path.join(backup_dir, fname)
        dst = os.path.join(results_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            restored += 1
        elif os.path.exists(dst):
            # backup had no file (real one didn't exist to begin with) -- remove
            # the panel copy so we don't leave synthetic data masquerading as real
            os.remove(dst)
    print(f"Restored {restored} real result files from backup.")


def swap_in_panel(results_dir, null_dir, method, asset_class, panel_idx):
    src = os.path.join(null_dir, f"null_panel_{asset_class}_{panel_idx:03d}.csv")
    if not os.path.exists(src):
        raise FileNotFoundError(
            f"Missing null panel file: {src}\n"
            f"Generate it first with compute_null_psd.py {asset_class} --n-panels >= {panel_idx+1}"
        )
    dst = os.path.join(results_dir, f"match_{method}_results_{asset_class}.csv")
    shutil.copy2(src, dst)


def mean_std_min_max(values):
    n = len(values)
    if n == 0:
        return (float('nan'),) * 4
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n if n > 1 else 0.0
    std = var ** 0.5
    return mean, std, min(values), max(values)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-panels", type=int, default=50)
    parser.add_argument("--tolerance", type=int, default=1, choices=[1, 2, 3],
                         help="tolerance 1 only is the anchored thesis claim; "
                              "override only for supplementary/curiosity checks")
    parser.add_argument("--method", default="psd", choices=["psd", "pacf", "wavelet"])
    parser.add_argument("--car-script", default="CAR.py")
    parser.add_argument("--results-dir", default="psd_results")
    parser.add_argument("--null-dir", default=None,
                         help="defaults to <results-dir>/null_panels")
    parser.add_argument("--out-csv", default="car_null_wrapper_results.csv")
    args = parser.parse_args()

    null_dir = args.null_dir or os.path.join(args.results_dir, "null_panels")
    backup_dir = os.path.join(args.results_dir, "_real_backup")

    if not os.path.exists(args.car_script):
        print(f"ERROR: CAR.py not found at {args.car_script}")
        sys.exit(1)

    real_result = None
    per_panel_rows = []

    backup_real_files(args.results_dir, args.method, backup_dir)

    try:
        # --- Step 1: real CAR number, from the backed-up real files, same code path ---
        print(f"\nComputing REAL CAR at tolerance +-{args.tolerance} (from backed-up real files) "
              f"via unmodified CAR.py...")
        restore_real_files(args.results_dir, args.method, backup_dir)  # put real files back first
        real_result = run_car(args.car_script, args.method, args.tolerance)
        if real_result:
            print(f"  real CAR={real_result['car_pct']:.2f}%  "
                  f"z={real_result['z']:.2f}  p={real_result['p']:.2e}")

        # --- Step 2: null panels ---
        print(f"\nRunning {args.n_panels} synthetic null panels at tolerance +-{args.tolerance}...")
        for panel_idx in range(args.n_panels):
            for ac in ASSET_CLASSES:
                swap_in_panel(args.results_dir, null_dir, args.method, ac, panel_idx)

            parsed = run_car(args.car_script, args.method, args.tolerance)
            if parsed:
                per_panel_rows.append(dict(panel=panel_idx, **parsed))

            if (panel_idx + 1) % 10 == 0 or panel_idx == args.n_panels - 1:
                print(f"  panel {panel_idx+1}/{args.n_panels} done")

    finally:
        # --- Step 3: always restore, even on crash/interrupt ---
        restore_real_files(args.results_dir, args.method, backup_dir)

    # --- Aggregate and report ---
    if args.out_csv:
        with open(args.out_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['panel', 'tolerance', 'processed', 'car_pct', 'covered',
                              'expected_random', 'excess_pct', 'z', 'p'])
            for row in per_panel_rows:
                writer.writerow([row['panel'], args.tolerance, row['processed'],
                                  row['car_pct'], row['covered'], row['expected_random'],
                                  row['excess_pct'], row['z'], row['p']])
        print(f"\nPer-panel results written to {args.out_csv}")

    null_cars = [r['car_pct'] for r in per_panel_rows]
    mean, std, lo, hi = mean_std_min_max(null_cars)

    print("\n" + "=" * 72)
    print(f"NULL vs REAL COMPARISON -- method={args.method}, tolerance +-{args.tolerance}, "
          f"{args.n_panels} synthetic panels")
    print("=" * 72)
    if real_result:
        print(f"REAL CAR:  {real_result['car_pct']:.2f}%  "
              f"(analytic z={real_result['z']:.2f}, p={real_result['p']:.2e})")
    else:
        print("REAL CAR:  could not be computed (see warnings above)")
    print(f"NULL CAR:  mean={mean:.2f}%  std={std:.2f}%  range=[{lo:.2f}%, {hi:.2f}%]  "
          f"(n={len(null_cars)} panels)")
    if real_result and std > 0:
        mc_z = (real_result['car_pct'] - mean) / std
        n_ge = sum(1 for c in null_cars if c >= real_result['car_pct'])
        print(f"Real CAR is {mc_z:.2f} null-standard-deviations above the synthetic-noise mean")
        print(f"Null panels reaching or exceeding real CAR: {n_ge}/{len(null_cars)}")
        if mean >= real_result['car_pct']:
            print(f"*** WARNING: null mean ({mean:.2f}%) meets or exceeds real CAR "
                  f"({real_result['car_pct']:.2f}%) ***")
    print("=" * 72)


if __name__ == "__main__":
    main()