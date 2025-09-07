# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730905.svg)](https://doi.org/10.5281/zenodo.16730905)

This repository contains code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- code/                   - Python implementation of PSD/PACF/Wavelet cycle detection and matching algorithm, CAR/p-value calculations
- code_charts/            - Python implementations to generate Figures used in the whitepaper
- psd_results/            - Primary PSD match results (78.78% CAR, statistically significant, 1980-2024)
- wavelet_results/        - Cross-Method Wavelet match results (78.37% CAR, statistically significant, 1980-2024)
- pacf_results/           - Cross-Method PACF match results (71.19% CAR, not statistically significant, 1980-2024)
- psd_results.1980-2024/  - Cross-window results: 1980-2024, same as the folder psd_results/
- psd_results.1990-2024/  - Cross-window results: 1990-2024
- psd_results.2000-2024/  - Cross-window results: 2000-2024
- instrument_data_*.csv   - 245 instrument lists by asset class (eq-Equity, co-Commodity, ix-Index, fx-Forex, cr-Crypto)


## Reproducing Results
### 1. Install Requirements
   - Ensure you have Python 3.7+ installed. Then install the required packages:
   - `pip install pandas numpy scipy statsmodels PyWavelets`
     
### 2. Data Requirements
   - The scripts expect historical daily price data (CSV files with Date and close columns) for each instrument listed in the instrument_data_*.csv files.
   - Data files should be placed in a historical_data/ directory in the root of the repository.
   - Data can be sourced from providers like Yahoo!Finance or Bloomberg, our data was sourced from Yahoo!Finance.

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
- Input instrument metadata in folder `instrument_data`
- Input historical data used from 1980-2025 (not included due to size)
- Output match_psd_results_*.csv files in folder `psd_results`, each file contains universal cycle matches and corresponding deltas 
- CAR Results For PSD (tolerance=2):
   - PSD Results (tolerance=2):
   - Instruments with cycles detected: 245
   - CAR: 78.78% (193 instruments)
   - Expected random coverage: 173.7 instruments
   - Excess coverage: 7.88% points
   - Statistical significance: z=2.72, p=3.30e-03

The wavelet and PACF analysis provide additional validation with:
- CAR Results For Wavelet (tolerance=2):
   - Wavelet Results (tolerance=2):
   - Instruments with cycles detected: 245
   - CAR: 78.37% (192 instruments)
   - Statistical significance: p=0.00513
- CAR Results For PACF (tolerance=2):
   - PACF Results (tolerance=2):
   - Instruments with cycles detected: 243
   - CAR: 71.19% (173 instruments)
   - Expected random coverage: 172.3 instruments
   - Excess coverage: 0.30% points
   - Statistical significance: z=0.10, p=4.91e-01
