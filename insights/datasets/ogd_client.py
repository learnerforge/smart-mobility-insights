import logging
import requests
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

CKAN_BASE = "https://data.gov.in/api/3/action/"
TIMEOUT = 30


def ckan_action(action, params=None):
    url = urljoin(CKAN_BASE, action)
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error("OGD API error: %s", e)
        return None


def search_datasets(query, rows=10):
    return ckan_action("package_search", {"q": query, "rows": rows})


def show_dataset(dataset_id):
    return ckan_action("package_show", {"id": dataset_id})


def list_resources(dataset_id):
    result = show_dataset(dataset_id)
    if result and result.get("success"):
        return result["result"].get("resources", [])
    return []


def search_transport_datasets():
    return search_datasets("transport road", rows=50)
