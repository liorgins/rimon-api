import logging
from rimon_data_extractor import run_full_extraction, LEVEL_MAP

API_URL = "https://rimonapi.weevi.com/api/ekomcategories/md_GetStaticData?searchKey=categories&preventcaching=true&returnasstring=false"
# Set as 'INFO' or 'DEBUG'
VERBOSITY_LEVEL = 'INFO'

LEVEL_MAP = {
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG
}

def main():
    run_full_extraction(API_URL, LEVEL_MAP[VERBOSITY_LEVEL])

if __name__ == "__main__":
    main() 