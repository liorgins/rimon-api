API_URL = "https://rimonapi.weevi.com/api/ekomcategories/md_GetStaticData?searchKey=categories&preventcaching=true&returnasstring=false"
# Set as 'INFO' or 'DEBUG'
VERBOSITY_LEVEL = 'INFO'

import logging

LEVEL_MAP = {
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG
} 