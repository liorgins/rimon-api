import logging
from rimon_data_extractor import run_full_extraction

API_URL = "https://rimonapi.weevi.com/api/ekomcategories/md_GetStaticData?searchKey=categories&preventcaching=true&returnasstring=false"
VERBOSITY_LEVEL = logging.INFO  # Or logging.DEBUG

def main():
    run_full_extraction(API_URL, VERBOSITY_LEVEL)

if __name__ == "__main__":
    main() 