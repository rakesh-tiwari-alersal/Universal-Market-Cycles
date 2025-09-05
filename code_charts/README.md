# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730905.svg)](https://doi.org/10.5281/zenodo.16730905)

This directory contains supporting code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- Figure1_spiral_comparison.py (Python implementation to generate Figure1)
- Figure2_gann_comparison.py   (Python implementation to generate Figure2)
- Figure3_bitcoin_model.py     (Python implementation to generate Figure3)
- historical_data/             (Daily close price data for Bitcoin and S&P 500 in .csv)

## Reproducing Charts
### 1. Install Requirements
   - Ensure you have Python 3.7+ installed. Then install the required packages:
   - `pip install pandas numpy scipy statsmodels sklearn`

### 2. Generating Charts
   - Figure 1 - Run `python ./Figure1_spiral_comparison.py`
   - Figure 2 - Run `python ./Figure2_gann_comparison.py`
   - Figure 3 - Run `python ./Figure3_bitcoin_model.py`
