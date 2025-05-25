import os
import json
import csv
from glob import glob

def get_latest_run_dirs(logs_dir="logs"):
    if not os.path.exists(logs_dir):
        raise FileNotFoundError(f"Logs directory '{logs_dir}' does not exist.")
    run_dirs = [d for d in glob(os.path.join(logs_dir, '*')) if os.path.isdir(d)]
    if len(run_dirs) < 2:
        raise FileNotFoundError("Not enough run directories found in logs/ to compare.")
    # Sort by directory name (timestamp format)
    sorted_runs = sorted(run_dirs)
    return sorted_runs[-2], sorted_runs[-1]

def load_raw_data(run_dir):
    raw_path = os.path.join(run_dir, 'raw', 'raw_data.json')
    with open(raw_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_sections(data):
    base = data['staticData']['data']['country_118']['primaryLang']
    categories = base.get('categories', {}).get('Data', [])
    products = base.get('products', [])
    return categories, products

def dictify_by_id(items):
    return {str(item.get('id', '')): item for item in items}

def diff_items(old, new):
    old_dict = dictify_by_id(old)
    new_dict = dictify_by_id(new)
    added = [v for k, v in new_dict.items() if k not in old_dict]
    removed = [v for k, v in old_dict.items() if k not in new_dict]
    changed = [v for k, v in new_dict.items() if k in old_dict and v != old_dict[k]]
    return added, removed, changed

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_csv(items, path):
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

def create_delta_structure():
    prev_run, curr_run = get_latest_run_dirs()
    delta_dir = os.path.join(curr_run, 'Delta')
    csv_dir = os.path.join(delta_dir, 'csv')
    json_dir = os.path.join(delta_dir, 'json')
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    prev_data = load_raw_data(prev_run)
    curr_data = load_raw_data(curr_run)

    prev_categories, prev_products = extract_sections(prev_data)
    curr_categories, curr_products = extract_sections(curr_data)

    # Categories
    cat_added, cat_removed, cat_changed = diff_items(prev_categories, curr_categories)
    save_json(cat_added, os.path.join(json_dir, 'categories_added.json'))
    save_json(cat_removed, os.path.join(json_dir, 'categories_removed.json'))
    save_json(cat_changed, os.path.join(json_dir, 'categories_changed.json'))
    save_csv(flatten_categories(cat_added), os.path.join(csv_dir, 'categories_added.csv'))
    save_csv(flatten_categories(cat_removed), os.path.join(csv_dir, 'categories_removed.csv'))
    save_csv(flatten_categories(cat_changed), os.path.join(csv_dir, 'categories_changed.csv'))

    # Products
    prod_added, prod_removed, prod_changed = diff_items(prev_products, curr_products)
    save_json(prod_added, os.path.join(json_dir, 'products_added.json'))
    save_json(prod_removed, os.path.join(json_dir, 'products_removed.json'))
    save_json(prod_changed, os.path.join(json_dir, 'products_changed.json'))
    save_csv(prod_added, os.path.join(csv_dir, 'products_added.csv'))
    save_csv(prod_removed, os.path.join(csv_dir, 'products_removed.csv'))
    save_csv(prod_changed, os.path.join(csv_dir, 'products_changed.csv'))

    # Categories hierarchy (hierarchical delta)
    def get_hierarchy(categories):
        return [clean_category_for_hierarchy(cat) for cat in categories]
    prev_hier = get_hierarchy(prev_categories)
    curr_hier = get_hierarchy(curr_categories)
    # For hierarchy, just show added/removed/changed root categories
    hier_added, hier_removed, hier_changed = diff_items(prev_hier, curr_hier)
    save_json(hier_added, os.path.join(json_dir, 'categories_hierarchy_added.json'))
    save_json(hier_removed, os.path.join(json_dir, 'categories_hierarchy_removed.json'))
    save_json(hier_changed, os.path.join(json_dir, 'categories_hierarchy_changed.json'))
    save_csv(flatten_hierarchy_for_csv(hier_added), os.path.join(csv_dir, 'categories_hierarchy_added.csv'))
    save_csv(flatten_hierarchy_for_csv(hier_removed), os.path.join(csv_dir, 'categories_hierarchy_removed.csv'))
    save_csv(flatten_hierarchy_for_csv(hier_changed), os.path.join(csv_dir, 'categories_hierarchy_changed.csv'))

    print(f"Delta files created in: {delta_dir}")

if __name__ == "__main__":
    create_delta_structure() 