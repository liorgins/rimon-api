import json
import csv
import os
import requests
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
import time

# Logger setup
class VerboseLogger:
    def __init__(self, log_file, level=logging.INFO):
        self.logger = logging.getLogger("RimonLogger")
        self.logger.handlers = []  # Remove any existing handlers to prevent duplicates
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
        self.file_handler = logging.FileHandler(log_file, encoding='utf-8')
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(self.formatter)
        self.console_handler.setLevel(level)
        self.logger.addHandler(self.console_handler)
        self.level = level
    def debug(self, msg):
        self.logger.debug(msg)
    def info(self, msg):
        self.logger.info(msg)
    def error(self, msg):
        self.logger.error(msg)
    def set_level(self, level):
        self.console_handler.setLevel(level)
        self.level = level

def fetch_from_api(url: str, logger: VerboseLogger) -> Optional[Dict]:
    """Fetch data from API and save to JSON file."""
    try:
        logger.info("Fetching data from API...")
        logger.debug(f"Fetching data from: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        logger.info("Data successfully received from API.")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        return None

def flatten_categories(categories: List[Dict], parent_title: str = None) -> List[Dict]:
    """Flatten the category hierarchy into a list of categories with parent information."""
    flattened = []
    
    for category in categories:
        flat_category = {
            'category_name': category.get('title', ''),
            'parent_category': parent_title,
            'id': category.get('id', ''),
            'url_title': category.get('urlTitle', ''),
            'description': category.get('description', ''),
            'show_on_homepage': category.get('showOnHomepage', False),
            'show_on_menu': category.get('showOnMenu', False),
            'priority': category.get('priority', 0),
            'image_src': category.get('imgSrc', '')
        }
        flattened.append(flat_category)
        
        # Process subcategories if they exist
        if 'Data' in category and category['Data']:
            sub_categories = flatten_categories(category['Data'], category['title'])
            flattened.extend(sub_categories)
    
    return flattened

def clean_category_for_hierarchy(category: Dict) -> Dict:
    """Clean category data for hierarchical export."""
    cleaned = {
        'id': category.get('id', ''),
        'title': category.get('title', ''),
        'urlTitle': category.get('urlTitle', ''),
        'description': category.get('description', ''),
        'showOnHomepage': category.get('showOnHomepage', False),
        'showOnMenu': category.get('showOnMenu', False),
        'priority': category.get('priority', 0),
        'imgSrc': category.get('imgSrc', '')
    }
    
    if 'Data' in category and category['Data']:
        cleaned['subcategories'] = [clean_category_for_hierarchy(cat) for cat in category['Data']]
    else:
        cleaned['subcategories'] = []
    
    return cleaned

def process_data(data: Dict, logger: VerboseLogger):
    start_time = time.time()
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        logger.info("Creating main logs directory (logs)")
        os.makedirs(logs_dir)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = os.path.join(logs_dir, f"{timestamp}")
    logger.info(f"Creating results directory: {results_dir}")
    os.makedirs(results_dir, exist_ok=True)
    # Create 'raw' subdirectory
    raw_dir = os.path.join(results_dir, 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    json_dir = os.path.join(raw_dir, 'json')
    csv_dir = os.path.join(raw_dir, 'csv')
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)
    log_file = os.path.join(raw_dir, 'run.log')
    logger.debug(f"Log file: {log_file}")
    base_data = data['staticData']['data']['country_118']['primaryLang']
    categories = base_data.get('categories', {}).get('Data', [])
    products = base_data.get('products', [])
    raw_data_json = os.path.join(raw_dir, 'raw_data.json')
    categories_csv = os.path.join(csv_dir, 'categories.csv')
    categories_json = os.path.join(json_dir, 'categories.json')
    categories_hierarchy_json = os.path.join(json_dir, 'categories-hierarchy.json')
    categories_hierarchy_csv = os.path.join(csv_dir, 'categories-hierarchy.csv')
    products_csv = os.path.join(csv_dir, 'products.csv')
    products_json = os.path.join(json_dir, 'products.json')
    logger.info("Exporting categories...")
    flattened_categories = flatten_categories(categories)
    hierarchical_categories = [clean_category_for_hierarchy(cat) for cat in categories]
    if flattened_categories:
        logger.info("Saving categories as CSV")
        fieldnames = flattened_categories[0].keys()
        with open(categories_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_categories)
        logger.debug(f"Categories CSV created successfully: {categories_csv}")
    with open(categories_json, 'w', encoding='utf-8') as f:
        json.dump(flattened_categories, f, indent=2)
    logger.info("Saving categories as JSON")
    logger.debug(f"Categories JSON created successfully: {categories_json}")
    with open(categories_hierarchy_json, 'w', encoding='utf-8') as f:
        json.dump(hierarchical_categories, f, indent=2)
    logger.info("Saving categories hierarchy as JSON")
    logger.debug(f"Categories hierarchy JSON created successfully: {categories_hierarchy_json}")
    def flatten_hierarchy_for_csv(categories, parent_id=None):
        # Flatten the hierarchical categories for CSV export, adding parent_id.
        rows = []
        for cat in categories:
            row = {
                'id': cat.get('id', ''),
                'title': cat.get('title', ''),
                'urlTitle': cat.get('urlTitle', ''),
                'description': cat.get('description', ''),
                'showOnHomepage': cat.get('showOnHomepage', False),
                'showOnMenu': cat.get('showOnMenu', False),
                'priority': cat.get('priority', 0),
                'imgSrc': cat.get('imgSrc', ''),
                'parent_id': parent_id
            }
            rows.append(row)
            if cat.get('subcategories'):
                rows.extend(flatten_hierarchy_for_csv(cat['subcategories'], cat.get('id', '')))
        return rows
    hierarchy_flat = flatten_hierarchy_for_csv(hierarchical_categories)
    if hierarchy_flat:
        logger.info("Saving categories hierarchy as CSV")
        fieldnames = hierarchy_flat[0].keys()
        with open(categories_hierarchy_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(hierarchy_flat)
        logger.debug(f"Categories hierarchy CSV created successfully: {categories_hierarchy_csv}")
    logger.info("Exporting products...")
    if products:
        logger.info("Saving products as CSV")
        fieldnames = products[0].keys()
        with open(products_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)
        logger.debug(f"Products CSV created successfully: {products_csv}")
    with open(products_json, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2)
    logger.info("Saving products as JSON")
    logger.debug(f"Products JSON created successfully: {products_json}")
    with open(raw_data_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info("Saving RAW DATA file")
    logger.debug(f"Raw data JSON created successfully: {raw_data_json}")
    elapsed = time.time() - start_time
    logger.info("")
    logger.info(f"Run summary:")
    logger.info(f"Results directory: {results_dir}")
    logger.info(f"Total categories: {len(flattened_categories)}")
    logger.info(f"Total products: {len(products)}")
    logger.info(f"Elapsed time: {elapsed:.2f} seconds")
    logger.debug("Run finished.")

if __name__ == "__main__":
    API_URL = "https://rimonapi.weevi.com/api/ekomcategories/md_GetStaticData?searchKey=categories&preventcaching=true&returnasstring=false"
    temp_logger = logging.getLogger("TempLogger")
    temp_logger.handlers = []  # Remove any existing handlers to prevent duplicates
    temp_logger.addHandler(logging.StreamHandler())
    temp_logger.setLevel(logging.INFO)
    temp_logger.info("Starting run...")
    data = fetch_from_api(API_URL, VerboseLogger('/dev/null'))
    if data is None:
        temp_logger.error("Failed to fetch data from API")
        exit(1)
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = os.path.join(logs_dir, f"{timestamp}")
    os.makedirs(results_dir, exist_ok=True)
    raw_dir = os.path.join(results_dir, 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    log_file = os.path.join(raw_dir, 'run.log')
    logger = VerboseLogger(log_file, level=logging.INFO)
    process_data(data, logger) 