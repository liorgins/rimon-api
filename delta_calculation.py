import os
import json
import csv
import logging
from glob import glob

# Logger setup
logger = logging.getLogger("DeltaLogger")
logger.handlers = []
logger.setLevel(logging.DEBUG)

def setup_logger(log_path):
    """Set up a logger that logs both to file and to console, with INFO and DEBUG levels."""
    # Remove all handlers before adding new ones
    logger.handlers = []
    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    # No return value

def get_latest_run_dirs(logs_dir="logs"):
    """Return the two latest run directories inside the logs directory for comparison purposes."""
    run_dirs = [d for d in glob(os.path.join(logs_dir, '*')) if os.path.isdir(d)]
    logger.debug(f"Found run directories: {run_dirs}")
    if len(run_dirs) < 2:
        logger.error("Not enough run directories found in logs/ to compare.")
        raise FileNotFoundError("Not enough run directories found in logs/ to compare.")
    sorted_runs = sorted(run_dirs)
    return sorted_runs[-2], sorted_runs[-1]

def get_raw_dir(run_dir):
    """Return the path to the 'Raw' directory inside a run directory. Raises if not found."""
    # Only accept 'Raw' (capital R) directory
    raw_dir = os.path.join(run_dir, 'Raw')
    if os.path.isdir(raw_dir):
        return raw_dir
    logger.error(f"No 'Raw' directory found in {run_dir}")
    raise FileNotFoundError(f"No 'Raw' directory found in {run_dir}")

def get_delta_dirs():
    """Return the current run directory and paths to Delta, csv, and json subdirectories for the latest run."""
    _, curr_run = get_latest_run_dirs()
    delta_dir = os.path.join(curr_run, 'Delta')
    csv_dir = os.path.join(delta_dir, 'csv')
    json_dir = os.path.join(delta_dir, 'json')
    return curr_run, delta_dir, csv_dir, json_dir

def create_delta_structure():
    """Create the Delta/csv and Delta/json folder structure for the latest run, and set up logging."""
    curr_run, delta_dir, csv_dir, json_dir = get_delta_dirs()
    logger.debug(f"Creating Delta structure at: {delta_dir}")
    os.makedirs(delta_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)
    log_path = os.path.join(delta_dir, 'delta.log')
    logger.debug(f"Creating delta.log at: {log_path}")
    setup_logger(log_path)
    logger.info(f"Created Delta structure at: {delta_dir}\n  - {csv_dir}\n  - {json_dir}")
    return curr_run, delta_dir, csv_dir, json_dir

def load_raw_data(run_dir):
    """Load the raw_data.json file from the given run directory."""
    raw_dir = get_raw_dir(run_dir)
    raw_path = os.path.join(raw_dir, 'raw_data.json')
    logger.debug(f"Loading raw_data.json from: {raw_path}")
    with open(raw_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_sections(data):
    """Extract categories and products sections from the loaded raw data."""
    base = data['staticData']['data']['country_118']['primaryLang']
    categories = base.get('categories', {}).get('Data', [])
    products = base.get('products', [])
    logger.debug(f"Extracted {len(categories)} categories, {len(products)} products")
    logger.debug(f"Category ids: {[c.get('id') for c in categories]}")
    logger.debug(f"Product ids: {[p.get('id') for p in products]}")
    return categories, products

def dictify_by_id(items):
    """Convert a list of dicts to a dict keyed by 'id'."""
    return {str(item.get('id', '')): item for item in items}

def diff_items(old, new):
    """Return lists of added, removed, and changed items between two lists of dicts (by id)."""
    old_dict = dictify_by_id(old)
    new_dict = dictify_by_id(new)
    added = [v for k, v in new_dict.items() if k not in old_dict]
    removed = [v for k, v in old_dict.items() if k not in new_dict]
    changed = [v for k, v in new_dict.items() if k in old_dict and v != old_dict[k]]
    logger.debug(f"diff_items: added ids: {[v.get('id') for v in added]}")
    logger.debug(f"diff_items: removed ids: {[v.get('id') for v in removed]}")
    logger.debug(f"diff_items: changed ids: {[v.get('id') for v in changed]}")
    return added, removed, changed

def save_json(data, path):
    """Save a Python object as a JSON file to the given path."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_csv(items, path):
    """Save a list of dicts as a CSV file to the given path. Writes header if items exist, else creates empty file."""
    if not items:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            f.write('')
        return
    fieldnames = items[0].keys()
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)

def flatten_categories(categories, parent_title=None):
    """Flatten a nested category structure into a flat list with parent information for CSV export."""
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
        if 'Data' in category and category['Data']:
            flattened.extend(flatten_categories(category['Data'], category['title']))
    return flattened

def clean_category_for_hierarchy(category):
    """Clean a category dict for hierarchical export, recursively including subcategories."""
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

def flatten_hierarchy_for_csv(categories, parent_id=None):
    """Flatten a hierarchical category structure for CSV export, including parent_id references."""
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

def get_prev_and_curr_runs():
    """Return prev_run and curr_run directories, raise if not enough or if they are the same."""
    prev_run, curr_run = get_latest_run_dirs()
    if prev_run == curr_run:
        logger.error(f"prev_run and curr_run are the same! Delta calculation skipped. prev_run={prev_run}")
        return None, None
    return prev_run, curr_run

def calculate_and_save_category_delta(prev_categories, curr_categories, json_dir, csv_dir, logger):
    logger.info("Calculating category delta...")
    cat_added, cat_removed, cat_changed = diff_items(prev_categories, curr_categories)
    logger.debug("Saving categories delta outputs...")
    save_json(cat_added, os.path.join(json_dir, 'categories_added.json'))
    save_json(cat_removed, os.path.join(json_dir, 'categories_removed.json'))
    save_json(cat_changed, os.path.join(json_dir, 'categories_changed.json'))
    save_csv(flatten_categories(cat_added), os.path.join(csv_dir, 'categories_added.csv'))
    save_csv(flatten_categories(cat_removed), os.path.join(csv_dir, 'categories_removed.csv'))
    save_csv(flatten_categories(cat_changed), os.path.join(csv_dir, 'categories_changed.csv'))
    logger.info(f"Delta categories - added: {len(cat_added)}, removed: {len(cat_removed)}, changed: {len(cat_changed)}")

def calculate_and_save_product_delta(prev_products, curr_products, json_dir, csv_dir, logger):
    logger.info("Calculating product delta...")
    prod_added, prod_removed, prod_changed = diff_items(prev_products, curr_products)
    logger.debug("Saving products delta outputs...")
    save_json(prod_added, os.path.join(json_dir, 'products_added.json'))
    save_json(prod_removed, os.path.join(json_dir, 'products_removed.json'))
    save_json(prod_changed, os.path.join(json_dir, 'products_changed.json'))
    save_csv(prod_added, os.path.join(csv_dir, 'products_added.csv'))
    save_csv(prod_removed, os.path.join(csv_dir, 'products_removed.csv'))
    save_csv(prod_changed, os.path.join(csv_dir, 'products_changed.csv'))
    logger.info(f"Delta products - added: {len(prod_added)}, removed: {len(prod_removed)}, changed: {len(prod_changed)}")

def calculate_and_save_hierarchy_delta(prev_categories, curr_categories, json_dir, csv_dir, logger):
    logger.info("Calculating hierarchy delta...")
    def get_hierarchy(categories):
        return [clean_category_for_hierarchy(cat) for cat in categories]
    prev_hier = get_hierarchy(prev_categories)
    curr_hier = get_hierarchy(curr_categories)
    hier_added, hier_removed, hier_changed = diff_items(prev_hier, curr_hier)
    logger.debug("Saving hierarchy delta outputs...")
    save_json(hier_added, os.path.join(json_dir, 'categories_hierarchy_added.json'))
    save_json(hier_removed, os.path.join(json_dir, 'categories_hierarchy_removed.json'))
    save_json(hier_changed, os.path.join(json_dir, 'categories_hierarchy_changed.json'))
    save_csv(flatten_hierarchy_for_csv(hier_added), os.path.join(csv_dir, 'categories_hierarchy_added.csv'))
    save_csv(flatten_hierarchy_for_csv(hier_removed), os.path.join(csv_dir, 'categories_hierarchy_removed.csv'))
    save_csv(flatten_hierarchy_for_csv(hier_changed), os.path.join(csv_dir, 'categories_hierarchy_changed.csv'))
    logger.info(f"Delta hierarchy files created.")

def calculate_delta():
    """Main function to calculate the delta (added/removed/changed) for categories, products, and hierarchy between the two latest runs. Outputs results as JSON and CSV."""
    logger.info("=== calculate_delta: START ===")
    try:
        curr_run, delta_dir, csv_dir, json_dir = create_delta_structure()
        logger.debug(f"Delta structure created. Delta dir: {delta_dir}")
        prev_run, curr_run = get_prev_and_curr_runs()
        if not prev_run or not curr_run:
            logger.error(f"Delta calculation skipped: prev_run and curr_run are the same! {prev_run}")
            return
        prev_data = load_raw_data(prev_run)
        curr_data = load_raw_data(curr_run)
        logger.debug("Loaded both raw_data.json files.")
        prev_categories, prev_products = extract_sections(prev_data)
        curr_categories, curr_products = extract_sections(curr_data)
        calculate_and_save_category_delta(prev_categories, curr_categories, json_dir, csv_dir, logger)
        calculate_and_save_product_delta(prev_products, curr_products, json_dir, csv_dir, logger)
        calculate_and_save_hierarchy_delta(prev_categories, curr_categories, json_dir, csv_dir, logger)
        logger.info(f"Delta files created in: {delta_dir}")
        logger.info("=== calculate_delta: END ===")
    except Exception as e:
        logger.error(f"Exception in calculate_delta: {e}")

if __name__ == "__main__":
    create_delta_structure()
    calculate_delta() 