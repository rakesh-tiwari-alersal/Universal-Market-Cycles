# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730905.svg)](https://doi.org/10.5281/zenodo.16730905)

This repository contains code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- code/                   - Python implementation of PSD/PACF/Wavelet cycle detection and matching algorithm, CAR/p-value calculations
- instrument_data/        - 245 instrument lists by asset class (eq-Equity, co-Commodity, ix-Index, fx-Forex, cr-Crypto)
- psd_results/            - Primary PSD match results (78.78% CAR, statistically significant, 1980-2024)
- wavelet_results/        - Cross-Method Wavelet match results (78.37% CAR, statistically significant, 1980-2024)
- pacf_results/           - Cross-Method PACF match results (71.19% CAR, not statistically significant)
- psd_results.1980-2024/  - Cross-window results: 1980-2024, same as the folder psd_results/
- psd_results.1990-2024/  - Cross-window results: 1990-2024
- psd_results.2000-2024/  - Cross-window results: 2000-2024

## Reproducing Results
### 1. Install Requirements
   - Ensure you have Python 3.7+ installed. Then install the required packages:
   - `pip install pandas numpy scipy statsmodels PyWavelets`
