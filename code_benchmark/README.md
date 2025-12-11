# Alersal Market Cycles Research Repository - Benchmark 
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730905.svg)](https://doi.org/10.5281/zenodo.16730905)

This directory contains supporting code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- historical_data/             - Contains daily close prices for Bitcoin and Gold as .csv
- compute_bitcoin_AIC.py       - Python implementation to generate AIC optimized lags for Bitcoin
- compute_bitcoin_R2.py        - Python implementation to generate out-of-sample R^2 for AIC optimized lags
- compute_gold_AIC.py          - Python implementation to generate AIC optimized lags for Gold
- compute_gold_R2.py           - Python implementation to generate out-of-sample R^2 for AIC optimized lags

## Reproducing Benchamark Table
### 1. Install Requirements
   - Ensure you have Python 3.7+ installed. Then install the required packages:
   - `pip install pandas numpy sklearn`

### 2. Generating Benchmark Data 
- Run the scripts from the code_benchmark (this) directory. The output will be displayed on the screen:
   - Generate Bitcoin benchmark (Lags and R^2):
      - Run `python .\compute_bitcoin_AIC.py`
      - Run `python .\compute_bitcoin_R2.py`
   - Generate gold benchmark (Lags and R^2):
      - Run `python .\compute_gold_AIC.py`
      - Run `python .\compute_gold_R2.py`
