# Alersal Market Cycles Research Repository
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16730906.svg)](https://doi.org/10.5281/zenodo.16730906)

This repository contains code and data for the whitepaper:  
**"Deriving Market Cycles from the Plastic Number to Model Volatility"**


## Structure
.
├── code/
│   ├── compute_match_psd.py   # PSD cycle detection per asset class
│   └── CAR.py                 # Coverage Acceptance Ratio calculator
├── instrument_data/
│   ├── eq.csv                 # Equity instruments
│   ├── ix.csv                 # Index instruments
│   ├── co.csv                 # Commodity instruments
│   ├── fx.csv                 # Forex instruments
│   └── cr.csv                 # Crypto instruments
├── psd_results/               # Precomputed matching results (78% CAR)
└── misc_files/                # Market correction history

## Reproducing Results
1. Install requirements:  
   `pip install pandas numpy scipy csv`
2. Run cycle detection with eq|ix|co|cr|fx as argument one-by-one
   python code/compute_match_psd.py eq  # Equities
   
   python code/compute_match_psd.py ix  # Indices
   
   python code/compute_match_psd.py co  # Commodities
   
   python code/compute_match_psd.py fx  # Forex
   
   python code/compute_match_psd.py cr  # Crypto
   Expected Output:
      psd_results/match_psd_results_<asset_class>.csv
4. Run to generate CAR and p-value -t 1|2|3 (tolerance, default=2)
   python code/CAR.py -t 2  # Default tolerance (±2 days)
   Expected output:
      PSD Results (tolerance=2, n=255):
      CAR: 77.65% (198 instruments)
      Expected random coverage: 179.3 instruments
      Excess coverage: 7.33% points
      Statistical significance: z=2.56, p=5.38e-03
   
## Verification
All results in the whitepaper's Appendix D were generated using:
   Instrument metadata from instrument_data/
   Cycle detection via compute_match_psd.py
   Statistical validation with CAR.py
   Tolerance window: ±2 days (unless specified)
   Data Note: Historical prices (1980-2025) sourced from Yahoo!Finance. Use instrument symbols in the CSV files with any financial data API.

## Key Features
   53 universal cycles derived from plastic number mathematics
   78% coverage across 255 instruments (equities, commodities, forex, crypto)
   Statistically significant: p<0.01 at tolerance=±1
   Ready-to-use AR models:
   # Bitcoin model from whitepaper (Sec 5.3)
   Y_t = ϕ₀ + ϕ₁Y_{t-196} + ϕ₂Y_{t-23} + ε_t

