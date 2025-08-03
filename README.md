# Alersal Market Cycles Research Repository

This repository contains code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**

## Structure
```
code/                   - Python implementation of PSD cycle detection and matching algorithm
instrument_data/        - Instrument lists by asset class (eq-Equity, co-Commodity, ix-Index, fx-Forex, cr-Crypto)
psd_results/            - Cycle matching results (86% CAR)

## Reproducing Results
1. Install requirements:  
   `pip install pandas numpy scipy csv`
2. Run cycle detection:  
   `python code/compute_match_psd.py <asset_class>`  
   Example: `python code/compute_match_psd.py eq`

## Verification
All empirical results in the whitepaper's Appendix B were generated using:
- `compute_match_psd.py`
- Instrument metadata in folder `instrument_data`
- Historical data used from 1980-2025 (not included due to size)
- Produces a .csv file with cycle matches and corresponding delta

# Link to whitepaper
- https://alersal.us/AlersalWhitepaper.pdf
