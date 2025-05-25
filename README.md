# Rimon Data Extractor

## Overview
This project extracts data from the Rimon API, processes it into structured files (categories, products, etc.), and saves all results in timestamped log folders. It also supports delta calculation between runs to track changes in the data.

## Setup
1. **Clone the repository**
2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Extraction
Run the main script:
```bash
python main.py
```
This will:
- Fetch data from the Rimon API
- Save all results in a new folder under `logs/<timestamp>`
- Create a `Raw` subfolder with all raw outputs (CSV, JSON, raw_data.json, run.log)
- Create a `Delta` folder (directly under the run folder) with CSV/JSON files showing the differences from the previous run

## Output Structure
```
logs/
  <timestamp>/
    Raw/
      csv/
      json/
      raw_data.json
      run.log
    Delta/
      csv/
      json/
      delta.log
```
- **Raw**: Contains all the extracted and processed data for the run
- **Delta**: Contains the differences (added/removed/changed) for categories, products, and hierarchy compared to the previous run

## Delta Calculation
After each run, the delta calculation compares the current run's raw data to the previous run. It outputs:
- `categories_added/removed/changed` (CSV & JSON)
- `products_added/removed/changed` (CSV & JSON)
- `categories_hierarchy_added/removed/changed` (CSV & JSON)

## Controlling Verbosity
You can control the log verbosity by editing `main.py`:
```python
VERBOSITY_LEVEL = 'INFO'  # or 'DEBUG'
```

## Notes
- The project is case-insensitive regarding the `Raw` folder (accepts both `Raw` and `raw`).
- All logs are saved both to the console and to log files in each run.
- Make sure to run the scripts from the project root directory.

## License
MIT 