import logging
from rimon_data_extractor import run_full_extraction, LEVEL_MAP
from delta_calculation import create_delta_structure, calculate_delta
from create_eng_heb_dictionary import main as create_dictionary_main
from compare_product_changes import compare_products

API_URL = "https://rimonapi.weevi.com/api/ekomcategories/md_GetStaticData?searchKey=categories&preventcaching=true&returnasstring=false"
# Set as 'INFO' or 'DEBUG'
VERBOSITY_LEVEL = 'INFO'

def main():
    run_full_extraction(API_URL, LEVEL_MAP[VERBOSITY_LEVEL])
    create_delta_structure()
    calculate_delta()
    create_dictionary_main()
    compare_products()

if __name__ == "__main__":
    main() 