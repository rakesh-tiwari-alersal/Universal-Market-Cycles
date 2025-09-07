# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730905.svg)](https://doi.org/10.5281/zenodo.16730905)

This directory contains general purpose tools for the whitepaper
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- historical_data/             - Contains daily close prices for Bitcoin, US Dollar Index, and Gold as .csv
- yule_walker/                 - Python implementations to calculate Yule Walker coefficients
- download_yf_data.py          - Python implementation download data from Yahoo!Finance.
- 
## Tools
### 1. Install Requirements
   - Ensure you have Python 3.7+ installed. Then install the required packages:
   - `pip install pandas numpy scipy statsmodels sklearn`

### 2. Downloading Data 
- The script will download files into a folder called historical_data/ for instruments listed in instrument_data.csv file.
   - Run `python download_yf_data.py <start_year> <end_year>`
   - For example: `python download_yf_data.py 1980 2024`
         
### 3. Calculating Yule Walker Coefficients



