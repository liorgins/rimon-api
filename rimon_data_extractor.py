import json
import csv
import os
import requests
from datetime import datetime
from typing import List, Dict, Optional, Tuple

def fetch_from_api(url: str) -> Optional[Dict]:
    """Fetch data from API and save to JSON file."""
    try:
        # Send GET request to the API
        print(f"Fetching data from: {url}")
        response = requests.get(url)
        
        # Raise an exception for bad status codes
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Save JSON data to file with timestamp
       
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None, None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None, None

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

def process_data(data: Dict):
    """Process and export data to various formats."""
    # Ensure logs directory exists (but do not recreate if exists)
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Generate readable timestamp for folder name (up to seconds, no milliseconds)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = os.path.join(logs_dir, f"{timestamp}")
    os.makedirs(results_dir, exist_ok=True)

    # Create subdirectories for JSON and CSV
    json_dir = os.path.join(results_dir, 'json')
    csv_dir = os.path.join(results_dir, 'csv')
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)

    # Define filenames with paths
    raw_data_json = os.path.join(results_dir, 'raw_data.json')
    categories_csv = os.path.join(csv_dir, 'categories.csv')
    categories_json = os.path.join(json_dir, 'categories.json')
    categories_hierarchy_json = os.path.join(json_dir, 'categories-hierarchy.json')
    categories_hierarchy_csv = os.path.join(csv_dir, 'categories-hierarchy.csv')
    products_csv = os.path.join(csv_dir, 'products.csv')
    products_json = os.path.join(json_dir, 'products.json')
    
    # Navigate to the relevant data
    base_data = data['staticData']['data']['country_118']['primaryLang']
    categories = base_data.get('categories', {}).get('Data', [])
    products = base_data.get('products', [])
    
    # Process and export categories
    flattened_categories = flatten_categories(categories)
    
    # Create hierarchical categories
    hierarchical_categories = [clean_category_for_hierarchy(cat) for cat in categories]
    
    # Export categories to CSV
    if flattened_categories:
        fieldnames = flattened_categories[0].keys()
        with open(categories_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_categories)
        print(f"Categories CSV created successfully: {categories_csv}")
    
    # Export flat categories to JSON
    with open(categories_json, 'w', encoding='utf-8') as f:
        json.dump(flattened_categories, f, indent=2)
    print(f"Categories JSON created successfully: {categories_json}")
    
    # Export hierarchical categories to JSON
    with open(categories_hierarchy_json, 'w', encoding='utf-8') as f:
        json.dump(hierarchical_categories, f, indent=2)
    print(f"Categories hierarchy JSON created successfully: {categories_hierarchy_json}")
    
    # Export hierarchical categories to CSV (flattened)
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
    hierarchy_flat = flatten_hierarchy_for_csv(hierarchical_categories)
    if hierarchy_flat:
        fieldnames = hierarchy_flat[0].keys()
        with open(categories_hierarchy_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(hierarchy_flat)
        print(f"Categories hierarchy CSV created successfully: {categories_hierarchy_csv}")
    
    # Export products to CSV
    if products:
        fieldnames = products[0].keys()
        with open(products_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)
        print(f"Products CSV created successfully: {products_csv}")
    
    # Export products to JSON
    with open(products_json, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2)
    print(f"Products JSON created successfully: {products_json}")

    # Export raw data to JSON
    with open(raw_data_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Raw data JSON created successfully: {raw_data_json}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Results directory: {results_dir}")
    print(f"Total categories exported: {len(flattened_categories)}")
    print(f"Total products exported: {len(products)}")

if __name__ == "__main__":
    # API URL
    API_URL = "https://rimonapi.weevi.com/api/ekomcategories/md_GetStaticData?searchKey=categories&preventcaching=true&returnasstring=false"
    
    # Fetch data from API
    data = fetch_from_api(API_URL)
    if data is None:
        print("Failed to fetch data from API")
        exit(1)
    
    # Process the data
    process_data(data) 