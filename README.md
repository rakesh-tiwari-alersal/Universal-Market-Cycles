# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730906.svg)](https://doi.org/10.5281/zenodo.16730906)

This repository contains code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- code/                   - Python implementation of PSD/PACF cycle detection and matching algorithm, CAR/p-value calculations
- instrument_data/        - 245 instrument lists by asset class (eq-Equity, co-Commodity, ix-Index, fx-Forex, cr-Crypto)
- psd_results/            - PSD match results (77% CAR)
- pacf_results/           - PACF match results (70% CAR, not statistically significant)
- misc_files/             - Auxiliary files (spiral.py, CAR output for Table 3)

## Reproducing Results
### 1. Install Requirements
   - Ensure you have Python 3.7+ installed. Then install the required packages:
   - `bash pip install pandas numpy scipy statsmodels`

### 2. For PSD Analysis
- Run cycle detection command with eq | ix | co | cr | fx as argument one-by-one
   - `python code/compute_match_psd.py eq`
   - `python code/compute_match_psd.py ix`
   - `python code/compute_match_psd.py co`
   - `python code/compute_match_psd.py cr`
   - `python code/compute_match_psd.py fx`
   - This generates match_psd_results_*.csv files in the psd_results/ directory.
- Calculate CAR and p-values (default tolerance=2)
   - Run to generate CAR and p-value -t 1 | 2 | 3 (tolerance, default is -t=2)
   - `python code/CAR.py psd -t 2`
     
### 3. For PACF Analysis
- Similarily, run cycle detection command with eq | ix | co | cr | fx as argument one-by-one
   - `python code/compute_match_pacf.py eq`
   - `python code/compute_match_pacf.py ix`
   - `python code/compute_match_pacf.py co`
   - `python code/compute_match_pacf.py cr`
   - `python code/compute_match_pacf.py fx`
   - This generates match_pacf_results_*.csv files in the pacf_results/ directory.
- Calculate CAR and p-values (example with tolerance=2)
   - `python code/CAR.py pacf -t 2`

## Verification
All empirical results in the whitepaper's Appendix D were generated using:
- `compute_match_psd.py` and `CAR.py` in folder `code`
- Input instrument metadata in folder `instrument_data`
- Input historical data used from 1980-2025 (not included due to size)
- Output match_psd_results_*.csv files in folder `psd_results`, each file contains universal cycle matches and corresponding deltas 
- CAR output :
   - PSD Results (tolerance=2):
   - Instruments with cycles detected: 245
   - CAR: 77.14% (189 instruments)
   - Expected random coverage: 173.5 instruments
   - Excess coverage: 6.32% points
   - Statistical significance: z=2.18, p=1.60e-02
