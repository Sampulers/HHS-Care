# Care Transition Efficiency & Placement Outcome Analytics

This repository contains a Streamlit dashboard for exploring care-transition and placement-outcome data for the HHS program.

## Project structure

- [HHS-Care.py](HHS-Care.py) — the main dashboard app
- [processed_dataset_with_new_columns.csv](processed_dataset_with_new_columns.csv) — the processed dataset used by the dashboard
- [HHS_Unaccompanied_Alien_Children_Program.csv](HHS_Unaccompanied_Alien_Children_Program.csv) — the source data file
- [requirements.txt](requirements.txt) — Python dependencies

## Setup

1. Create and activate a Python environment:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`

2. Install dependencies:
   - `pip install -r requirements.txt`

3. Run the app:
   - `streamlit run HHS-Care.py`

4. Optional environment variables:
   - Copy [.env.example](.env.example) to [.env](.env) and update any local values you need.
   - The app does not require secrets to run locally, but this keeps private settings out of the repository.

## What the app shows

- KPI cards for transfer efficiency, discharge rate, throughput, and backlog pressure
- Trend charts for transfer and discharge performance
- Funnel and bottleneck visualizations
- A full dataset table for reviewing the processed data
