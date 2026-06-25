# Alersal Market Cycles Research Repository - Benchmark 
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730905.svg)](https://doi.org/10.5281/zenodo.16730905)

This directory contains supporting code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- historical_data/            - Contains daily close prices for IBM and DAX Index as .csv
- compute_ibm_AIC.py          - Python implementation to generate AIC optimized lags for IBM
- compute_ibm_R2.py           - Python implementation to generate out-of-sample R^2 using AIC optimized lags
- compute_daxindex_AIC.py     - Python implementation to generate AIC optimized lags for DAX Index
- compute_daxindex_R2.py      - Python implementation to generate out-of-sample R^2 using AIC optimized lags

## Reproducing Benchmark Table
### 1. Install Requirements
   - Ensure you have Python 3.7+ installed. Then install the required packages:
   - `pip install pandas numpy sklearn`

### 2. Generating Benchmark Data 
- Run the scripts from the code_benchmark (this) directory. The output will be displayed on the screen:
   - Generate IBM benchmark (Lags and R^2):
      - Run `python compute_ibm_AIC.py`
      - Run `python compute_ibm_R2.py`
   - Generate DAX Index benchmark (Lags and R^2):
      - Run `python compute_daxindex_AIC.py`
      - Run `python compute_daxindex_R2.py`
