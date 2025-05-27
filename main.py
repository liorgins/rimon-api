# Backup branch before destructive git reset (created by Ziv)
import logging
from rimon_data_extractor import run_full_extraction
from delta_calculation import calculate_delta
from create_eng_heb_dictionary import main as create_dictionary_main
from compare_product_changes import compare_delta
from config import API_URL, VERBOSITY_LEVEL, LEVEL_MAP

def main():
    run_full_extraction(API_URL, LEVEL_MAP[VERBOSITY_LEVEL])  # Fetches data from the API and saves all outputs and logs for this run
    calculate_delta()  # Compares the latest two runs and outputs added/removed/changed products and categories
    compare_delta()  # Compares changed products between runs and outputs a CSV with field-level changes
    create_dictionary_main()  # Generates English-Hebrew dictionary CSVs for products and categories


if __name__ == "__main__":
    main() 