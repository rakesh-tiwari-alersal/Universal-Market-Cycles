# Alersal Market Cycles Research Repository - Tools
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730905.svg)](https://doi.org/10.5281/zenodo.16730905)

This directory contains general purpose tools for the whitepaper

**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- download_yf_data.py          - Downloads historical data from Yahoo!Finance
- compute_yw_coeff_generic.py  - Calculates Yule-Walker coefficients with Plastic Cycle filtering
- compute_yw_R2.py             - Computes out-of-sample R-squared for model validation
- instrument_data.csv          - Contains initial list of 245 instruments

## Installation
- Python 3.7+ required
- Install packages: `pip install pandas numpy scipy scikit-learn yfinance`

## Tools

### 1. Data Download (download_yf_data.py)
  - Downloads historical price data for instruments listed in instrument_data.csv
  - Creates historical_data/ folder with CSV files and download_logs/ with reports
  - Usage: `python download_yf_data.py [start_year] [end_year]`

### 2. Coefficient Calculator (compute_yw_coeff_generic.py)
  - Calculates Yule-Walker autoregressive coefficients for any financial instrument
  - Optional filtering for 47 predefined Plastic Cycles with -p flag
  - Usage: `python compute_yw_coeff_generic.py -f FILE.csv BEGIN END [-d N] [-p]`

### 3. Model Validator (compute_yw_R2.py)
  - Computes out-of-sample R-squared values for model validation
  - Tests polynomial degrees 1, 3, and 4 for optimal fit assessment
  - Usage: `python compute_yw_R2.py -f FILE.csv -l LAG1,LAG2,LAG3`

## Basic Workflow
1. Add/Delete instruments to instrument_data.csv
2. Download data: `python download_yf_data.py 1980 2024`
3. Find cycles: `python compute_yw_coeff_generic.py -f BTC-USD.csv 190 250 -p`
4. Validate model: `python compute_yw_R2.py -f GC=F.csv -l 24,291,385`
