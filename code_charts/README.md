# Alersal Market Cycles Research Repository - Charts 
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730905.svg)](https://doi.org/10.5281/zenodo.16730905)

This directory contains supporting code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Directory Structure
- historical_data/             - Contains daily close prices for Bitcoin, US Dollar Index, and Gold as .csv
- yule_walker/                 - Python implementations to calculate Yule Walker coefficients
- Figure1_spiral_comparison.py - Python implementation to generate Figure1
- Figure2_bitcoin_model.py     - Python implementation to generate Figure2
- Figure3_usdollar_model.py    - Python implementation to generate Figure3
- Figure4_gold_model.py        - Python implementation to generate Figure4

## Reproducing Charts
### 1. Install Requirements
   - Ensure you have Python 3.7+ installed. Then install the required packages:
   - `pip install pandas numpy scipy statsmodels sklearn matplotlib`

### 2. Generating Charts 
- Run the scripts from the code_charts (this) directory. The generated images will be saved in the same directory:
   - Generate Figure 1 (Spiral Comparison):
      - Run `python Figure1_spiral_comparison.py`
   - Generate Figure 2 (Bitcoin Model):
      - Run `python Figure2_bitcoin_model.py`
   - Generate Figure 3 (US Dollar Model):
      - Run `python Figure3_usdollar_model.py`
   - Generate Figure 4 (Gold Model):
      - Run `python Figure4_gold_model.py`
         
### 3. Calculating Yule Walker Coefficients
- Run the scripts from the code_charts (this) directory. Output shows all coefficients in the input range, and the top 3 most significant lags.
   - Basic usage with default differencing:
      - `python yule_walker/compute_yw_coeff_bitcoin.py 190 250`
   - With second-order differencing:
      - `python yule_walker/compute_yw_coeff_bitcoin.py 190 250 -d 2`
   - Filtered to only show Plastic Number cycles:
      - `python yule_walker/compute_yw_coeff_bitcoin.py 190 250 -p`
