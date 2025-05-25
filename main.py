import logging
from rimon_data_extractor import fetch_from_api, process_data, VerboseLogger

API_URL = "https://rimonapi.weevi.com/api/ekomcategories/md_GetStaticData?searchKey=categories&preventcaching=true&returnasstring=false"

# Set verbosity level here: logging.INFO or logging.DEBUG
VERBOSITY_LEVEL = logging.INFO

def main():
    temp_logger = logging.getLogger("TempLogger")
    temp_logger.handlers = []
    temp_logger.addHandler(logging.StreamHandler())
    temp_logger.setLevel(VERBOSITY_LEVEL)
    temp_logger.info("Starting run...")
    data = fetch_from_api(API_URL, VerboseLogger('/dev/null', level=VERBOSITY_LEVEL))
    if data is None:
        temp_logger.error("Failed to fetch data from API")
        exit(1)
    # Prepare output/logging structure
    import os
    from datetime import datetime
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = os.path.join(logs_dir, f"{timestamp}")
    os.makedirs(results_dir, exist_ok=True)
    raw_dir = os.path.join(results_dir, 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    log_file = os.path.join(raw_dir, 'run.log')
    logger = VerboseLogger(log_file, level=VERBOSITY_LEVEL)
    process_data(data, logger)

if __name__ == "__main__":
    main() 