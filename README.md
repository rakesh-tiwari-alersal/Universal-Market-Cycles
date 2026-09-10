# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730905.svg)](https://doi.org/10.5281/zenodo.16730905)

This repository contains code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Risk-Price Geometry"**

## Directory Structure
- code/                   - Python implementation of PSD/PACF/Wavelet cycle detection and matching algorithm, CAR/p-value calculations
- code_benchmark/         - Python implementations to generate Benchmark data used in the whitepaper
- code_charts/            - Python implementations to generate Figures used in the whitepaper
- code_randomized_tests/  - Python implementations to reproduce random data tests in the whitepaper
- psd_results/            - Primary PSD match results (statistically significant, 2000-2025. Also used for randomized tests)
- wavelet_results/        - Cross-Method Wavelet match results (statistically significant, 2000-2025)
- pacf_results/           - Cross-Method PACF match results (statistically insignificant, 2000-2025)
- psd_results.1990-2025/  - Cross-window results: 1990-2025
- psd_results.2000-2025/  - Cross-window results: 2000-2025 (same as the folder psd_results/)
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
      - `python tools/download_yf_data.py 2000 2025`
 
### 3. For PSD Analysis
- Run cycle detection command with eq | ix | co | cr | fx as argument one-by-one
   - `python code/compute_match_psd.py eq`
   - `python code/compute_match_psd.py ix`
   - `python code/compute_match_psd.py co`
   - `python code/compute_match_psd.py cr`
   - `python code/compute_match_psd.py fx`
   - This generates match_psd_results_*.csv files in the psd_results/ directory.
- Calculate CAR and p-values (default tolerance=1)
   - Run to generate CAR and p-value -t 1 | 2 | 3 (tolerance, default is -t=1)
   - `python code/CAR.py psd -t 1`
     
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
- Calculate CAR and p-values (example with tolerance=3)
   - `python code/CAR.py pacf -t 3`
   
### 6. For Null PSD Analysis
- Run null cycle detection command with eq | ix | co | cr | fx as argument one-by-one
   - `python code_randomized_tests/compute_null_psd.py eq`
   - `python code_randomized_tests/compute_null_psd.py ix`
   - `python code_randomized_tests/compute_null_psd.py co`
   - `python code_randomized_tests/compute_null_psd.py cr`
   - `python code_randomized_tests/compute_null_psd.py fx`
   - This generates GBM synthetic *.csv files in the psd_results/null_panels directory.
- Calculate CAR and z-scores (tolerance=1) for random data and random table tests respectively.
   - `python code_randomized_test/CAR_RandomData.py --car-script code/CAR.py`
   - `python code_randomized_test/CAR_RandomTable.py --car-script code/CAR.py`

## Verification - CAR 
All empirical results in the whitepaper's Appendix D were generated using:
- `compute_match_psd.py` and `CAR.py` in folder `code`
- Input instrument metadata in files `instrument_data*.csv`
- Input historical data used from 2000-2025 (not included due to size)
- Output match_psd_results_*.csv files in folder `psd_results`, each file contains universal cycle matches and corresponding deltas 
- CAR PSD Results (tolerance=1):
   - Instruments with cycles detected: 240
   - CAR: 67.92% (163 instruments)
   - Expected random coverage: 105.4 instruments
   - Excess coverage: 24.01% points
   - Statistical significance: z=7.49, p=5.55e-14
   
## Verification - Randomized CAR
- CAR Random Data Results
   - REAL CAR:  67.92%  (analytic z=7.49, p=5.55e-14)
   - NULL CAR:  mean=57.08%  std=3.41%  range=[48.75%, 64.58%]  (n=50 panels)
   - Real CAR is 3.18 null-standard-deviations above the synthetic-noise mean
   - Null panels reaching or exceeding real CAR: 0/50
- CAR Random Table Results
   - Table 3 CAR:  67.92%
   - Random tables CAR:  mean=43.06%  std=12.59%  range=[14.17%, 71.67%]  (n=200)
   - Table 3 is 1.97 standard deviations above the random-table mean
   - Random tables reaching or exceeding Table 3's CAR: 4/200  (empirical p <= 0.0200)
