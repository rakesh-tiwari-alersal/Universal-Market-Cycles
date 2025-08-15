# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730906.svg)](https://doi.org/10.5281/zenodo.16730906)

This repository contains code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**
code/                   - Python implementation of PSD cycle detection and matching algorithm, CAR calculations
instrument_data/        - Instrument lists by asset class (eq-Equity, co-Commodity, ix-Index, fx-Forex, cr-Crypto)
psd_results/            - Cycle matching results (78% CAR)
misc_files/             - Market correction history (.xls)

## Reproducing Results
1. Install requirements:  
   `pip install pandas numpy scipy csv`
2. Run cycle detection with eq|ix|co|cr|fx as argument one-by-one
   `python code/compute_match_psd.py <asset_class>`  
   Example: `python code/compute_match_psd.py eq`
3. Run to generate CAR and p-value -t 1|2|3 (tolerance, default=2)
   Example: `python code/CAR.py`
   Expected Output:
   53 universal cycles derived from plastic number mathematics
   78% coverage across 255 instruments (equities, commodities, forex, crypto)
   Statistically significant: p<0.01 at tolerance=±1

## Verification
All empirical results in the whitepaper's Appendix D were generated using:
- `compute_match_psd.py` and `CAR.py` 
- Instrument metadata in folder `instrument_data`
- Historical data used from 1980-2025 (not included due to size)
- Produces a .csv file with cycle matches and corresponding delta
