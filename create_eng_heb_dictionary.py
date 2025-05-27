import os
import csv
from glob import glob
from datetime import datetime
import logging

try:
    from googletrans import Translator
    translator = Translator()
    def translate_to_hebrew(text):
        """Translate English text to Hebrew using googletrans, or return empty string if not available."""
        try:
            result = translator.translate(text, src='en', dest='he')
            logger.debug(f"Translating '{text}' -> '{result.text}'")
            return result.text
        except Exception as e:
            logger.error(f"Translation failed for '{text}': {e}")
            return ''
except ImportError:
    print("googletrans is not installed. Please run: pip install googletrans==4.0.0-rc1")
    def translate_to_hebrew(text):
        logger.warning(f"Translation skipped for '{text}' (googletrans not installed)")
        return ''

try:
    from config import GENERATE_DICTIONARY
except ImportError:
    GENERATE_DICTIONARY = True  # Default if config.py is missing

# Logger setup
logger = logging.getLogger("DictionaryLogger")
logger.handlers = []
logger.setLevel(logging.DEBUG)
log_dir = 'eng-heb-dictionary'
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, 'dictionary.log')
file_handler = logging.FileHandler(log_path, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

def get_latest_csv_dir():
    """Return the path to the latest run's Raw/csv directory inside logs/."""
    logs_dir = 'logs'
    run_dirs = [d for d in glob(os.path.join(logs_dir, '*')) if os.path.isdir(d)]
    if not run_dirs:
        logger.error('No run directories found in logs/.')
        raise FileNotFoundError('No run directories found in logs/.')
    latest_run = sorted(run_dirs)[-1]
    csv_dir = os.path.join(latest_run, 'Raw', 'csv')
    if not os.path.isdir(csv_dir):
        logger.error(f'No csv directory found in {latest_run}/Raw/')
        raise FileNotFoundError(f'No csv directory found in {latest_run}/Raw/')
    return csv_dir

def extract_products(csv_path):
    """Extract product id, sku, and title from a products CSV file."""
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
    """Load an existing dictionary CSV file and return a dict keyed by (id, sku)."""
    existing = {}
    if os.path.exists(dict_path):
        with open(dict_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row.get('id', ''), row.get('sku', ''))
                existing[key] = row
    return existing

def write_products_dictionary(products, out_path, auto_translate=True):
    """
    Write a products dictionary CSV with English and Hebrew columns, auto-translating only new products.
    Only products whose IDs are not already in the dictionary will be translated and added.
    """
    # 1. Load existing dictionary and collect all translated product IDs
    existing = load_existing_dictionary(out_path)
    translated_ids = set(key[0] for key in existing.keys())  # key is (id, sku)

    # 2. Collect all product IDs from the new products list
    all_new_ids = set(prod['id'] for prod in products)

    # 3. Log the comparison
    logger.info(f"Comparing {len(all_new_ids)} product IDs from latest run to {len(translated_ids)} already translated IDs in dictionary...")
    intersection = all_new_ids & translated_ids
    ids_to_translate = all_new_ids - translated_ids
    logger.info(f"{len(intersection)} products already translated (will be skipped). {len(ids_to_translate)} new products will be translated.")

    # 4. Filter products to only those needing translation
    products_to_translate = [prod for prod in products if prod['id'] in ids_to_translate]

    new_rows = []
    translated_count = 0
    for prod in products_to_translate:
        key = (prod['id'], prod['sku'])
        heb = translate_to_hebrew(prod['english']) if auto_translate else ''
        if heb:
            translated_count += 1
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
    return len(new_rows), translated_count

def main():
    """Main function to generate English-Hebrew dictionary CSVs for products, categories, and category hierarchy from the latest run's CSVs."""
    if not GENERATE_DICTIONARY:
        logger.info("Skipping dictionary generation (GENERATE_DICTIONARY=False in config.py)")
        return

    csv_dir = get_latest_csv_dir()
    out_dir = 'eng-heb-dictionary'
    os.makedirs(out_dir, exist_ok=True)

    # Products
    products_csv = os.path.join(csv_dir, 'products.csv')
    products_dict_csv = os.path.join(out_dir, 'products_dictionary.csv')
    products_written = 0
    products_translated = 0
    if os.path.exists(products_csv):
        products = extract_products(products_csv)
        written, translated = write_products_dictionary(products, products_dict_csv, auto_translate=True)
        products_written += written
        products_translated += translated

    # Categories
    categories_csv = os.path.join(csv_dir, 'categories.csv')
    categories_written = 0
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
                    logger.debug(f"Translating category '{val}' -> '{heb}'")
                    writer.writerow([val, heb])
                    categories_written += 1

    # Categories hierarchy
    categories_hier_csv = os.path.join(csv_dir, 'categories-hierarchy.csv')
    hierarchy_written = 0
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
                    logger.debug(f"Translating hierarchy title '{val}' -> '{heb}'")
                    writer.writerow([val, heb])
                    hierarchy_written += 1

    logger.info(f"Dictionaries created in: {out_dir}")
    logger.info(f"Products written: {products_written}, products translated: {products_translated}")
    logger.info(f"Categories written: {categories_written}")
    logger.info(f"Hierarchy titles written: {hierarchy_written}")

if __name__ == "__main__":
    main() 