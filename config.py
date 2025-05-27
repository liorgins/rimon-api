import logging

# API URL for fetching categories data
API_URL = "https://rimonapi.weevi.com/api/ekomcategories/md_GetStaticData?searchKey=categories&preventcaching=true&returnasstring=false"

# Default verbosity level for logging
VERBOSITY_LEVEL = 'INFO'

# Map of logging levels to use in the code (INFO, DEBUG)
LEVEL_MAP = {
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG
}

# Flag to control whether to generate the English-Hebrew dictionary
GENERATE_DICTIONARY = False 