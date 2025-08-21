# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730906.svg)](https://doi.org/10.5281/zenodo.16730906)

This repository contains code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- code/                   - Python implementation of PSD/PACF cycle detection and matching algorithm, CAR/p-value calculations
- instrument_data/        - 245 instrument lists by asset class (eq-Equity, co-Commodity, ix-Index, fx-Forex, cr-Crypto)
- psd_results/            - PSD match results (77% CAR)
- pacf_results/           - PACF match results (71% CAR)
- misc_files/             - Auxiliary files (spiral.py, CAR output for Table 3)

## Reproducing Results
- Install requirements:  
   - `pip install pandas numpy scipy csv`
- Run cycle detection with eq | ix | co | cr | fx as argument one-by-one
   - `python code/compute_match_psd.py eq`
   - `python code/compute_match_psd.py ix`
   - `python code/compute_match_psd.py co`
   - `python code/compute_match_psd.py cr`
   - `python code/compute_match_psd.py fx`
- Run to generate CAR and p-value -t 1 | 2 | 3 (tolerance, default is -t=2)
   - `python code/CAR.py`

## Verification
All empirical results in the whitepaper's Appendix D were generated using:
- `compute_match_psd.py` and `CAR.py` in folder `code`
- Input instrument metadata in folder `instrument_data`
- Input historical data used from 1980-2025 (not included due to size)
- Output match_psd_results_*.csv files in folder `psd_results`, each file contains universal cycle matches and corresponding deltas 
- CAR output :
   - PSD Results (tolerance=2):
   - Instruments with cycles detected: 245
   - CAR: 76.73% (188 instruments)
   - Expected random coverage: 172.3 instruments
   - Excess coverage: 6.42% points
   - Statistical significance: z=2.20, p=1.51e-02
