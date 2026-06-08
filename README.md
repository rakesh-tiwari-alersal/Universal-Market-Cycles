# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730905.svg)](https://doi.org/10.5281/zenodo.16730905)

This repository contains code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- code/                   - Python implementation of PSD/PACF/Wavelet cycle detection and matching algorithm, CAR/p-value calculations
- code_benchmark/         - Python implementations to generate Benchmark data used in the whitepaper
- code_charts/            - Python implementations to generate Figures used in the whitepaper
- psd_results/            - Primary PSD match results (74.90% CAR, statistically significant, 2000-2025)
- wavelet_results/        - Cross-Method Wavelet match results (74.58% CAR, statistically significant, 2000-2025)
- pacf_results/           - Cross-Method PACF match results (67.08% CAR, statistically significant, 2000-2025)
- psd_results.1990-2025/  - Cross-window results: 1990-2025
- psd_results.2010-2025/  - Cross-window results: 2010-2025
- instrument_data_*.csv   - 240 instrument lists by asset class (eq-Equity, co-Commodity, ix-Index, fx-Forex, cr-Crypto)
- instrument_data.csv     - 240 instrument master-list for downloading only.
- tools/                  - General purpose tools to download data, other supporting scripts.

## Reproducing Results
### 1. Install Requirements
   - Ensure you have Python 3.7+ installed. Then install the required packages:
   - `pip install pandas numpy scipy statsmodels PyWavelets yfinance`
     
### 2. Data Requirements
   - The scripts expect historical daily price data (CSV files with Date and close columns) for each instrument listed in the instrument_data_*.csv files. Data files should be placed in a historical_data/ directory.
   - Data can be sourced from providers like Yahoo!Finance or Bloomberg, our data was sourced from Yahoo!Finance.
      - `python tools/download_yf_data 2000 2025`
 
### 3. For PSD Analysis
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
     
### 4. For Wavelet Analysis
- Similarly, run cycle detection command with eq | ix | co | cr | fx as argument one-by-one
   - `python code/compute_match_wavelet.py eq`
   - `python code/compute_match_wavelet.py ix`
   - `python code/compute_match_wavelet.py co`
   - `python code/compute_match_wavelet.py cr`
   - `python code/compute_match_wavelet.py fx`
   - This generates match_wavelet_results_*.csv files in the wavelet_results/ directory.
- Calculate CAR and p-values (example with tolerance=2)
   - `python code/CAR.py wavelet -t 2`
     
### 5. For PACF Analysis
- Similarly, run cycle detection command with eq | ix | co | cr | fx as argument one-by-one
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
- Input instrument metadata in files `instrument_data*.csv`
- Input historical data used from 2000-2025 (not included due to size)
- Output match_psd_results_*.csv files in folder `psd_results`, each file contains universal cycle matches and corresponding deltas 
- CAR PSD Results (tolerance=2):
   - Instruments with cycles detected: 239
   - CAR: 74.90% (179 instruments)
   - Expected random coverage: 146.0 instruments
   - Excess coverage: 13.79% points
   - Statistical significance: z=4.37, p=4.73e-06

The wavelet and PACF analysis provide additional validation with:
- CAR Results For Wavelet (tolerance=2):
   - Instruments with cycles detected: 240
   - CAR: 74.58% (179 instruments)
   - Expected random coverage: 146.7 instruments
   - Excess coverage: 13.48% points
   - Statistical significance: z=4.28, p=7.36e-06
- CAR Results For PACF (tolerance=2):
   - Instruments with cycles detected: 240
   - CAR: 67.08% (161 instruments)
   - Expected random coverage: 146.7 instruments
   - Excess coverage: 5.98% points
   - Statistical significance: z=1.90, p=3.24e-02


