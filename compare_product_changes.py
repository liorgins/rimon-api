import os
import csv
import json
from glob import glob

def get_latest_run_dirs(logs_dir="logs"):
    """Return the two latest run directories inside the logs directory for comparison purposes."""
    run_dirs = [d for d in glob(os.path.join(logs_dir, '*')) if os.path.isdir(d)]
    if len(run_dirs) < 2:
        raise FileNotFoundError("Not enough run directories found in logs/ to compare.")
    sorted_runs = sorted(run_dirs)
    return sorted_runs[-2], sorted_runs[-1]

def get_raw_data(run_dir):
    """Load the products section from raw_data.json in the given run directory and return a dict keyed by product id."""
    raw_path = os.path.join(run_dir, 'Raw', 'raw_data.json')
    with open(raw_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    products = data['staticData']['data']['country_118']['primaryLang'].get('products', [])
    return {str(p['id']): p for p in products}

def compare_products():
    """Compare changed products between the two latest runs and output a CSV with field-level changes for each product."""
    prev_run, curr_run = get_latest_run_dirs()
    delta_csv_dir = os.path.join(curr_run, 'Delta', 'csv')
    changed_csv = os.path.join(delta_csv_dir, 'products_changed.csv')
    output_csv = os.path.join(delta_csv_dir, 'products_field_changes.csv')

    prev_products = get_raw_data(prev_run)
    curr_products = get_raw_data(curr_run)

    with open(changed_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        changed_products = [row for row in reader]

    if not changed_products:
        print("No changed products found in products_changed.csv. Exiting.")
        return

    fieldnames = ['id', 'sku', 'title', 'field', 'old_value', 'new_value']
    rows = []
    for prod in changed_products:
        prod_id = str(prod['id'])
        prev = prev_products.get(prod_id, {})
        curr = curr_products.get(prod_id, {})
        for key in curr.keys():
            old_val = prev.get(key, '')
            new_val = curr.get(key, '')
            if old_val != new_val:
                rows.append({
                    'id': prod_id,
                    'sku': curr.get('sku', ''),
                    'title': curr.get('title', ''),
                    'field': key,
                    'old_value': old_val,
                    'new_value': new_val
                })
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote detailed product changes to: {output_csv}")

if __name__ == "__main__":
    compare_products() 