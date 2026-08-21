#!/usr/bin/env python3
"""
Figure_ibm_riskprice_model.v2.py

Publication-quality black-and-white illustration of:

    1. Daily Close Price
    2. Market Equilibrium
    3. Upper Plastic dislocation band
    4. Lower Plastic dislocation band

The Market Equilibrium construction is intentionally based on the
same rolling-window procedure used by plot_TF-Band.py.

For every available trading day:

    E_t = ALPHA * Y_(t-SHORT_CYCLE)
        + (1 - ALPHA) * Y_(t-LONG_CYCLE)

Then, for that day, a polynomial is fitted ONLY to the preceding
EQ_FRAMESIZE observations of E_t:

    window = E_t[i-EQ_FRAMESIZE : i]

The fitted polynomial is evaluated at the end of that window.

There is NO trading/position logic, no High/Low processing, no
model_selection.xlsx dependency, and no video generation.
"""

from __future__ import annotations

import argparse
import os
import sys

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ==========================================================
# CONSTANTS / DEFAULTS
# ==========================================================

# --------------------------
# Model defaults
# --------------------------
DEFAULT_LONG_CYCLE = 385
DEFAULT_SHORT_CYCLE = 23

# DATA_SLICE defaults to:
#     3 * LONG_CYCLE
EQ_FRAME_MULTIPLIER = 3

DEFAULT_POLY = 3
DEFAULT_ALPHA = 0.7
DEFAULT_N_YEARS = 5

# --------------------------
# Plastic dislocation bands
# --------------------------
# Band fractions indexed by Plastic k.
PLASTIC_BAND_VALUES = (
    0.3247,
    0.2451,
    0.1850,
    0.1397,
    0.1054,
    0.0796,
    0.0600,
)

# Defaults expressed as Plastic k values.
DEFAULT_UPPER_BAND1_K = 3       # 0.1397 = +13.97%
DEFAULT_LOWER_BAND1_K = 4       # 0.1054 = -10.54%
DEFAULT_UPPER_BAND2_K = 0       # 0.3247 = +32.47%
DEFAULT_LOWER_BAND2_K = 0       # 0.3247 = -32.47%

# --------------------------
# Allowed cycle ranges
# --------------------------
MIN_SHORT_CYCLE = 17
MAX_SHORT_CYCLE = 54

MIN_LONG_CYCLE = 219
MAX_LONG_CYCLE = 676

# --------------------------
# Output / figure
# --------------------------
OUTPUT_TEMPLATE = "Figure2_{symbol}_riskprice_model.png"

FIGSIZE = (14, 8)
DPI = 300

# --------------------------
# Line widths
# --------------------------
PRICE_LINEWIDTH = 1.0
EQUILIBRIUM_LINEWIDTH = 2.4
BAND_LINEWIDTH = 1.6

# --------------------------
# Typography
# --------------------------
TITLE_FONTSIZE = 20
AXIS_LABEL_FONTSIZE = 18
TICK_FONTSIZE = 12
LEGEND_FONTSIZE = 12

# --------------------------
# Grid / axes
# --------------------------
GRID_ALPHA = 0.50
Y_PADDING = 0.05


# ==========================================================
# ARGUMENT PARSING
# ==========================================================

def parse_lags(value: str) -> tuple[int, int]:
    """Parse -l SHORT,LONG."""
    parts = [part.strip() for part in value.split(",")]

    if len(parts) != 2:
        raise argparse.ArgumentTypeError(
            "-l/--lags must be SHORT,LONG, e.g. 23,385"
        )

    try:
        short_cycle = int(parts[0])
        long_cycle = int(parts[1])
    except ValueError:
        raise argparse.ArgumentTypeError(
            "-l/--lags must contain two integers, e.g. 23,385"
        )

    return short_cycle, long_cycle


def get_band_value(k: int, name: str) -> float:
    """Return the dislocation-band fraction for Plastic k."""
    if not 0 <= k < len(PLASTIC_BAND_VALUES):
        raise ValueError(
            f"{name} must be an integer k between "
            f"0 and {len(PLASTIC_BAND_VALUES) - 1}; got {k}"
        )

    return PLASTIC_BAND_VALUES[k]


# ==========================================================
# DATA UTILITIES
# ==========================================================

def resolve_data_path(filename: str) -> str:
    """
    Resolve the input CSV from historical_data/.

    -f accepts a filename such as IBM.csv.
    """
    filename = filename.strip()

    if not filename:
        raise ValueError("Input filename cannot be empty")

    path = os.path.join("historical_data", filename)

    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Input file not found: {path}"
        )

    return path


def find_column(df: pd.DataFrame, name: str) -> str:
    """Find a CSV column case-insensitively."""
    for column in df.columns:
        if column.strip().lower() == name.lower():
            return column

    raise ValueError(f"Required column '{name}' is missing")


def load_data(path: str) -> pd.DataFrame:
    """Load Date and Close from the historical CSV."""
    df = pd.read_csv(path)
    df.columns = [column.strip() for column in df.columns]

    date_col = find_column(df, "Date")
    close_col = find_column(df, "Close")

    df = df[[date_col, close_col]].copy()

    df.rename(
        columns={
            date_col: "Date",
            close_col: "Close",
        },
        inplace=True,
    )

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

    df.dropna(subset=["Date", "Close"], inplace=True)

    df.sort_values("Date", inplace=True)
    df.drop_duplicates(subset=["Date"], keep="last", inplace=True)
    df.reset_index(drop=True, inplace=True)

    if df.empty:
        raise ValueError("No valid Date/Close observations found")

    return df


# ==========================================================
# MARKET EQUILIBRIUM
# ==========================================================

def compute_equilibrium(
    df: pd.DataFrame,
    short_cycle: int,
    long_cycle: int,
    eq_framesize: int,
    poly_order: int,
    alpha: float,
) -> pd.DataFrame:
    """
    Compute the Market Equilibrium exactly from the rolling
    DATA_SLICE construction used in plot_TF-Band.py.

    Step 1:
        E_t = alpha * Close_(t-short)
            + (1-alpha) * Close_(t-long)

    Step 2:
        For EVERY day i, fit a polynomial using ONLY:

            E_t[i-eq_framesize : i]

        and evaluate that polynomial at:

            eq_framesize - 1

    Therefore the current E_t[i] is NOT included in the
    equilibrium estimate for day i.
    """
    result = df.copy()

    result["Y_short"] = result["Close"].shift(short_cycle)
    result["Y_long"] = result["Close"].shift(long_cycle)

    result["E_t"] = (
        alpha * result["Y_short"]
        + (1.0 - alpha) * result["Y_long"]
    )

    # This is the same logical operation as:
    #
    #     df = df.dropna(subset=["E_t"]).reset_index(drop=True)
    #
    # in plot_TF-Band.py.
    result = result.dropna(subset=["E_t"]).reset_index(drop=True)

    result["E_trend"] = np.nan

    # Exactly DATA_SLICE points are used for every polynomial fit.
    x = np.arange(eq_framesize, dtype=float)

    for i in range(eq_framesize, len(result)):

        window = result["E_t"].iloc[
            i - eq_framesize:i
        ].values

        coefficients = np.polyfit(
            x,
            window,
            poly_order,
        )

        polynomial = np.poly1d(coefficients)

        result.loc[
            result.index[i],
            "E_trend"
        ] = polynomial(eq_framesize - 1)

    return result


# ==========================================================
# PLOT
# ==========================================================

def create_plot(
    df: pd.DataFrame,
    symbol: str,
    n_years: int,
    upper_band1: float,
    lower_band1: float,
    upper_band2: float,
    lower_band2: float,
    upper_band1_k: int,
    lower_band1_k: int,
    upper_band2_k: int,
    lower_band2_k: int,
    output_path: str,
) -> None:
    """Create and save the thesis/book-quality figure."""

    # ------------------------------------------------------
    # Select the last N calendar years available in the CSV.
    # ------------------------------------------------------
    end_date = df["Date"].iloc[-1]
    start_date = end_date - pd.DateOffset(years=n_years)

    plot_df = df[
        df["Date"] >= start_date
    ].copy()

    if plot_df.empty:
        raise ValueError(
            f"No data available for the requested "
            f"{n_years}-year plotting period"
        )

    if plot_df["E_trend"].notna().sum() == 0:
        raise ValueError(
            "No Market Equilibrium observations are available "
            "in the requested plotting period"
        )

    # ------------------------------------------------------
    # Plastic dislocation bands
    # ------------------------------------------------------
    plot_df["Upper_Band1"] = (
        plot_df["E_trend"] * (1.0 + upper_band1)
    )

    plot_df["Lower_Band1"] = (
        plot_df["E_trend"] * (1.0 - lower_band1)
    )

    plot_df["Upper_Band2"] = (
        plot_df["E_trend"] * (1.0 + upper_band2)
    )

    plot_df["Lower_Band2"] = (
        plot_df["E_trend"] * (1.0 - lower_band2)
    )

    # ------------------------------------------------------
    # Figure
    # ------------------------------------------------------
    fig, ax = plt.subplots(
        figsize=FIGSIZE,
        facecolor="white",
    )

    ax.set_facecolor("white")

    # ------------------------------------------------------
    # DAILY CLOSE PRICE
    # ------------------------------------------------------
    # Thin, solid black line.
    #
    # This is the actual observed Close series from the CSV.
    # It is deliberately independent of the equilibrium series.
    ax.plot(
        plot_df["Date"],
        plot_df["Close"],
        color="black",
        linestyle="-",
        linewidth=PRICE_LINEWIDTH,
        label="Daily Close Price",
        zorder=1,
    )

    # ------------------------------------------------------
    # MARKET EQUILIBRIUM
    # ------------------------------------------------------
    # Thick, solid black line.
    #
    # NaN values before the first valid equilibrium observation
    # are naturally omitted by matplotlib.
    ax.plot(
        plot_df["Date"],
        plot_df["E_trend"],
        color="black",
        linestyle="-",
        linewidth=EQUILIBRIUM_LINEWIDTH,
        label="Market Equilibrium",
        zorder=3,
    )

    # ------------------------------------------------------
    # UPPER PLASTIC DISLOCATION BAND
    # ------------------------------------------------------
    ax.plot(
        plot_df["Date"],
        plot_df["Upper_Band1"],
        color="black",
        linestyle="--",
        linewidth=BAND_LINEWIDTH,
        label=f"Upper Plastic Bands (k={upper_band1_k}, k={upper_band2_k})",
        zorder=2,
    )

    # ------------------------------------------------------
    # LOWER PLASTIC DISLOCATION BAND
    # ------------------------------------------------------
    ax.plot(
        plot_df["Date"],
        plot_df["Lower_Band1"],
        color="black",
        linestyle="--",
        linewidth=BAND_LINEWIDTH,
        label=f"Lower Plastic Bands (k={lower_band1_k}, k={lower_band2_k})",
        zorder=2,
    )

    # ------------------------------------------------------
    # UPPER PLASTIC DISLOCATION BAND 2
    # ------------------------------------------------------
    ax.plot(
        plot_df["Date"],
        plot_df["Upper_Band2"],
        color="black",
        linestyle="--",
        linewidth=BAND_LINEWIDTH,
        label="_nolegend_",
        zorder=2,
    )

    # ------------------------------------------------------
    # LOWER PLASTIC DISLOCATION BAND 2
    # ------------------------------------------------------
    ax.plot(
        plot_df["Date"],
        plot_df["Lower_Band2"],
        color="black",
        linestyle="--",
        linewidth=BAND_LINEWIDTH,
        label="_nolegend_",
        zorder=2,
    )

    # ------------------------------------------------------
    # X AXIS
    # ------------------------------------------------------
    # YEARLY labels ONLY.
    #
    # No quarterly/monthly labels are ever used.
    ax.xaxis.set_major_locator(
        mdates.YearLocator()
    )
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )
    ax.set_xlim(plot_df["Date"].min(), plot_df["Date"].max())

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=TICK_FONTSIZE,
    )

    # ------------------------------------------------------
    # GRID
    # ------------------------------------------------------
    ax.grid(
        True,
        which="major",
        axis="both",
        alpha=GRID_ALPHA,
        linewidth=0.7,
    )

    # ------------------------------------------------------
    # LABELS / TITLE
    # ------------------------------------------------------
    ax.set_xlabel(
        "Trading Date →",
        fontsize=AXIS_LABEL_FONTSIZE,
        fontweight="bold",
        labelpad=10,
    )

    ax.set_ylabel(
        "Daily Close Price →",
        fontsize=AXIS_LABEL_FONTSIZE,
        fontweight="bold",
        labelpad=10,
    )

    ax.set_title(
        f"Illustration: {symbol} Asymmetric Risk-Price Structure with Plastic Bands",
        fontsize=TITLE_FONTSIZE,
        fontweight="bold",
        pad=14,
    )

    # ------------------------------------------------------
    # Y-AXIS PADDING
    # ------------------------------------------------------
    y_values = pd.concat(
        [
            plot_df["Close"],
            plot_df["E_trend"],
            plot_df["Upper_Band1"],
            plot_df["Lower_Band1"],
            plot_df["Upper_Band2"],
            plot_df["Lower_Band2"],
        ]
    ).dropna()

    y_min = y_values.min()
    y_max = y_values.max()
    y_range = y_max - y_min

    if y_range > 0:
        padding = y_range * Y_PADDING
        ax.set_ylim(
            y_min - padding,
            y_max + padding,
        )

    # ------------------------------------------------------
    # BOUNDED LEGEND
    # ------------------------------------------------------
    legend = ax.legend(
        loc="upper left",
        fontsize=LEGEND_FONTSIZE,
        frameon=True,
        fancybox=True,
        framealpha=1.0,
        facecolor="white",
        edgecolor="black",
        borderpad=0.8,
        labelspacing=0.6,
        handlelength=2.8,
        handletextpad=0.8,
    )

    legend.get_frame().set_linewidth(1.2)

    # ------------------------------------------------------
    # AXIS SPINES
    # ------------------------------------------------------
    for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_linewidth(1.0)

    # ------------------------------------------------------
    # SAVE
    # ------------------------------------------------------
    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=DPI,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)


# ==========================================================
# MAIN
# ==========================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Generate a black-and-white Plastic-model risk-price "
            "illustration with Daily Close Price, Market Equilibrium, "
            "and upper/lower dislocation bands."
        )
    )

    # ------------------------------------------------------
    # Required arguments
    # ------------------------------------------------------
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help=(
            "CSV filename in historical_data/, "
            "e.g. IBM.csv"
        ),
    )

    parser.add_argument(
        "-l",
        "--lags",
        required=True,
        type=parse_lags,
        metavar="SHORT,LONG",
        help=(
            "Plastic short,long cycles, "
            "e.g. 23,385"
        ),
    )

    # ------------------------------------------------------
    # Optional arguments
    # ------------------------------------------------------
    parser.add_argument(
        "-d",
        "--data-slice",
        type=int,
        default=None,
        help=(
            "Equilibrium DATA_SLICE / frame size; "
            "default: 3 * LONG_CYCLE"
        ),
    )

    parser.add_argument(
        "-p",
        "--poly",
        type=int,
        default=DEFAULT_POLY,
        help=f"Polynomial order; default: {DEFAULT_POLY}",
    )

    parser.add_argument(
        "-a",
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help=f"Equilibrium alpha; default: {DEFAULT_ALPHA}",
    )

    parser.add_argument(
        "-y",
        "--years",
        type=int,
        default=DEFAULT_N_YEARS,
        help=f"Number of trailing years; default: {DEFAULT_N_YEARS}",
    )

    parser.add_argument(
        "-u1",
        "--upper1",
        type=int,
        default=DEFAULT_UPPER_BAND1_K,
        help=(
            "Upper dislocation band 1 Plastic k; "
            f"default: {DEFAULT_UPPER_BAND1_K}"
        ),
    )

    parser.add_argument(
        "-w1",
        "--lower1",
        type=int,
        default=DEFAULT_LOWER_BAND1_K,
        help=(
            "Lower dislocation band 1 Plastic k; "
            f"default: {DEFAULT_LOWER_BAND1_K}"
        ),
    )

    parser.add_argument(
        "-u2",
        "--upper2",
        type=int,
        default=DEFAULT_UPPER_BAND2_K,
        help=(
            "Upper dislocation band 2 Plastic k; "
            f"default: {DEFAULT_UPPER_BAND2_K}"
        ),
    )

    parser.add_argument(
        "-w2",
        "--lower2",
        type=int,
        default=DEFAULT_LOWER_BAND2_K,
        help=(
            "Lower dislocation band 2 Plastic k; "
            f"default: {DEFAULT_LOWER_BAND2_K}"
        ),
    )

    args = parser.parse_args()

    # ======================================================
    # VALIDATION
    # ======================================================

    short_cycle, long_cycle = args.lags

    if not (
        MIN_SHORT_CYCLE
        <= short_cycle
        <= MAX_SHORT_CYCLE
    ):
        parser.error(
            f"SHORT cycle must be between "
            f"{MIN_SHORT_CYCLE} and {MAX_SHORT_CYCLE}; "
            f"got {short_cycle}"
        )

    if not (
        MIN_LONG_CYCLE
        <= long_cycle
        <= MAX_LONG_CYCLE
    ):
        parser.error(
            f"LONG cycle must be between "
            f"{MIN_LONG_CYCLE} and {MAX_LONG_CYCLE}; "
            f"got {long_cycle}"
        )

    if args.poly < 0:
        parser.error(
            "Polynomial order must be >= 0"
        )

    if not 0 <= args.alpha <= 1:
        parser.error(
            "Alpha must satisfy 0 <= alpha <= 1"
        )

    if args.years <= 0:
        parser.error(
            "Number of years must be > 0"
        )

    try:
        upper_band1 = get_band_value(args.upper1, "-u1/--upper1")
        lower_band1 = get_band_value(args.lower1, "-w1/--lower1")
        upper_band2 = get_band_value(args.upper2, "-u2/--upper2")
        lower_band2 = get_band_value(args.lower2, "-w2/--lower2")
    except ValueError as exc:
        parser.error(str(exc))

    # ------------------------------------------------------
    # DATA_SLICE
    # ------------------------------------------------------
    #
    # Default:
    #
    #     DATA_SLICE = 3 * LONG_CYCLE
    #
    eq_framesize = (
        args.data_slice
        if args.data_slice is not None
        else EQ_FRAME_MULTIPLIER * long_cycle
    )

    if eq_framesize <= 0:
        parser.error(
            "DATA_SLICE must be > 0"
        )

    if eq_framesize <= args.poly:
        parser.error(
            "DATA_SLICE must be greater than "
            "the polynomial order"
        )

    # ======================================================
    # LOAD / COMPUTE / PLOT
    # ======================================================

    try:
        data_path = resolve_data_path(args.file)

        df = load_data(data_path)

        # Need enough observations to construct E_t and then
        # obtain at least one DATA_SLICE-length polynomial fit.
        minimum_required = (
            long_cycle
            + eq_framesize
            + 1
        )

        if len(df) < minimum_required:
            raise ValueError(
                f"Insufficient data: {len(df)} observations available; "
                f"at least {minimum_required} are required for "
                f"LONG_CYCLE={long_cycle} and "
                f"DATA_SLICE={eq_framesize}"
            )

        # --------------------------------------------------
        # IMPORTANT:
        #
        # Equilibrium is computed over the FULL historical
        # series BEFORE selecting the last N years.
        #
        # This is necessary because the equilibrium for a
        # plotted date needs its full preceding lag/frame
        # history.
        # --------------------------------------------------
        df = compute_equilibrium(
            df=df,
            short_cycle=short_cycle,
            long_cycle=long_cycle,
            eq_framesize=eq_framesize,
            poly_order=args.poly,
            alpha=args.alpha,
        )

        symbol = os.path.splitext(
            os.path.basename(args.file)
        )[0].strip()

        # Output beside THIS PROGRAM.
        program_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        output_path = os.path.join(
            program_dir,
            OUTPUT_TEMPLATE.format(
                symbol=symbol
            ),
        )

        create_plot(
            df=df,
            symbol=symbol,
            n_years=args.years,
            upper_band1=upper_band1,
            lower_band1=lower_band1,
            upper_band2=upper_band2,
            lower_band2=lower_band2,
            upper_band1_k=args.upper1,
            lower_band1_k=args.lower1,
            upper_band2_k=args.upper2,
            lower_band2_k=args.lower2,
            output_path=output_path,
        )

    except (
        FileNotFoundError,
        ValueError,
        OSError,
    ) as exc:
        print(
            f"[ERROR] {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    # ======================================================
    # SUMMARY
    # ======================================================

    print()
    print("=== FIGURE CONFIGURATION ===")
    print(f"Symbol          : {symbol}")
    print(f"Short cycle     : {short_cycle}")
    print(f"Long cycle      : {long_cycle}")
    print(f"DATA_SLICE      : {eq_framesize}")
    print(f"Polynomial      : {args.poly}")
    print(f"Alpha           : {args.alpha}")
    print(f"Years plotted   : {args.years}")
    print(f"Upper band 1    : k={args.upper1} ({upper_band1:.2%})")
    print(f"Lower band 1    : k={args.lower1} ({lower_band1:.2%})")
    print(f"Upper band 2    : k={args.upper2} ({upper_band2:.2%})")
    print(f"Lower band 2    : k={args.lower2} ({lower_band2:.2%})")
    print(f"Output          : {output_path}")
    print("============================")
    print()


if __name__ == "__main__":
    main()
