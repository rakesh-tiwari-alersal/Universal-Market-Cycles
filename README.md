# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730906.svg)](https://doi.org/10.5281/zenodo.16730906)

This repository contains code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- code/                   - Python implementation of PSD cycle detection and matching algorithm, CAR/p-value calculations
- instrument_data/        - 255 instrument lists by asset class (eq-Equity, co-Commodity, ix-Index, fx-Forex, cr-Crypto)
- psd_results/            - PSD match results (77% CAR)
- misc_files/             - Auxiliary files (spiral.py)

## Reproducing Results
- Install requirements:  
   - `pip install pandas numpy scipy csv`
- Run cycle detection with eq | ix | co | cr | fx as argument one-by-one
   - `python code/compute_match_psd.py <asset_class>`  
   - Example: `python code/compute_match_psd.py eq`
- Run to generate CAR and p-value -t 1|2|3 (tolerance, default is -t=2)
   - Example: `python code/CAR.py`
   - Output:
      - PSD Results (tolerance=2, n=255):
      - CAR: 76.86% (196 instruments)
      - Statistical significance: z=2.29, p=1.19e-02

## Verification
All empirical results in the whitepaper's Appendix D were generated using:
- `compute_match_psd.py` and `CAR.py` in folder `code`
- Input instrument metadata in folder `instrument_data`
- Input historical data used from 1980-2025 (not included due to size)
- Output *.csv files with cycle matches and corresponding delta in folder `psd_results`
