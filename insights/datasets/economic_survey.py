import logging

import requests

logger = logging.getLogger(__name__)

TABLE_128_URL = "https://www.indiabudget.gov.in/budget2024-25/economicsurvey/doc/stat/tab1.28.xlsx"
TIMEOUT = 60


def fetch_table_128():
    try:
        resp = requests.get(TABLE_128_URL, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.content
    except requests.RequestException as e:
        logger.error("Failed to fetch Economic Survey Table 1.28: %s", e)
        return None
