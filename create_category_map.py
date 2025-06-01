import os
import csv
import json
from glob import glob

def find_latest_log_dir(logs_root):
    log_dirs = [d for d in os.listdir(logs_root) if os.path.isdir(os.path.join(logs_root, d))]
    log_dirs = sorted(log_dirs, reverse=True)
    if not log_dirs:
        raise Exception('No log directories found')
    return os.path.join(logs_root, log_dirs[0])

def build_category_map(categories_csv_path):
    category_map = {}
    with open(categories_csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            parent = row['parent_category'].strip()
            name = row['category_name'].strip()
            if parent not in category_map:
                category_map[parent] = []
            category_map[parent].append(name)
    return category_map

def main():
    logs_root = os.path.join(os.path.dirname(__file__), 'logs')
    latest_log = find_latest_log_dir(logs_root)
    categories_csv = os.path.join(latest_log, 'Raw', 'csv', 'categories.csv')
    if not os.path.exists(categories_csv):
        raise Exception(f'categories.csv not found at {categories_csv}')
    category_map = build_category_map(categories_csv)
    out_path = os.path.join(os.path.dirname(__file__), 'category_map.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(category_map, f, ensure_ascii=False, indent=2)
    print(f'Category map written to {out_path}')

if __name__ == '__main__':
    main() 