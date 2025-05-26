import os
import csv
from glob import glob
from datetime import datetime

try:
    from googletrans import Translator
    translator = Translator()
    def translate_to_hebrew(text):
        try:
            result = translator.translate(text, src='en', dest='he')
            print(f"Translating '{text}' -> '{result.text}'")
            return result.text
        except Exception as e:
            print(f"Translation failed for '{text}': {e}")
            return ''
except ImportError:
    print("googletrans is not installed. Please run: pip install googletrans==4.0.0-rc1")
    def translate_to_hebrew(text):
        print(f"Translation skipped for '{text}' (googletrans not installed)")
        return ''

def get_latest_csv_dir():
    logs_dir = 'logs'
    run_dirs = [d for d in glob(os.path.join(logs_dir, '*')) if os.path.isdir(d)]
    if not run_dirs:
        raise FileNotFoundError('No run directories found in logs/.')
    latest_run = sorted(run_dirs)[-1]
    csv_dir = os.path.join(latest_run, 'Raw', 'csv')
    if not os.path.isdir(csv_dir):
        raise FileNotFoundError(f'No csv directory found in {latest_run}/Raw/')
    return csv_dir

def extract_products(csv_path):
    products = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prod_id = row.get('id', '').strip()
            sku = row.get('sku', '').strip()
            title = row.get('title', '').strip()
            if prod_id and title:
                products.append({'id': prod_id, 'sku': sku, 'english': title})
    return products

def load_existing_dictionary(dict_path):
    existing = {}
    if os.path.exists(dict_path):
        with open(dict_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row.get('id', ''), row.get('sku', ''))
                existing[key] = row
    return existing

def write_products_dictionary(products, out_path, auto_translate=True):
    existing = load_existing_dictionary(out_path)
    new_rows = []
    for prod in products:
        key = (prod['id'], prod['sku'])
        if key in existing:
            continue  # Skip existing
        heb = translate_to_hebrew(prod['english']) if auto_translate else ''
        new_rows.append({
            'id': prod['id'],
            'sku': prod['sku'],
            'english': prod['english'],
            'hebrew': heb
        })
    # Write header if file doesn't exist, else append
    write_header = not os.path.exists(out_path)
    with open(out_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'sku', 'english', 'hebrew'])
        if write_header:
            writer.writeheader()
        for row in new_rows:
            writer.writerow(row)

def main():
    # Test translation
    print('Test translation for "Apple":', translate_to_hebrew('Apple'))

    csv_dir = get_latest_csv_dir()
    out_dir = 'eng-heb-dictionary'
    os.makedirs(out_dir, exist_ok=True)

    # Products
    products_csv = os.path.join(csv_dir, 'products.csv')
    products_dict_csv = os.path.join(out_dir, 'products_dictionary.csv')
    if os.path.exists(products_csv):
        products = extract_products(products_csv)
        write_products_dictionary(products, products_dict_csv, auto_translate=True)

    # Categories
    categories_csv = os.path.join(csv_dir, 'categories.csv')
    if os.path.exists(categories_csv):
        cat_names = set()
        with open(categories_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                val = row.get('category_name', '').strip()
                if val:
                    cat_names.add(val)
        from collections import OrderedDict
        cat_dict_path = os.path.join(out_dir, 'categories_dictionary.csv')
        existing = set()
        if os.path.exists(cat_dict_path):
            with open(cat_dict_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing.add(row.get('english', ''))
        with open(cat_dict_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if os.stat(cat_dict_path).st_size == 0:
                writer.writerow(['english', 'hebrew'])
            for val in sorted(cat_names):
                if val not in existing:
                    heb = translate_to_hebrew(val)
                    writer.writerow([val, heb])

    # Categories hierarchy
    categories_hier_csv = os.path.join(csv_dir, 'categories-hierarchy.csv')
    if os.path.exists(categories_hier_csv):
        hier_titles = set()
        with open(categories_hier_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                val = row.get('title', '').strip()
                if val:
                    hier_titles.add(val)
        hier_dict_path = os.path.join(out_dir, 'categories_hierarchy_dictionary.csv')
        existing = set()
        if os.path.exists(hier_dict_path):
            with open(hier_dict_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing.add(row.get('english', ''))
        with open(hier_dict_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if os.stat(hier_dict_path).st_size == 0:
                writer.writerow(['english', 'hebrew'])
            for val in sorted(hier_titles):
                if val not in existing:
                    heb = translate_to_hebrew(val)
                    writer.writerow([val, heb])

    print(f"Dictionaries created in: {out_dir}")

if __name__ == "__main__":
    main() 