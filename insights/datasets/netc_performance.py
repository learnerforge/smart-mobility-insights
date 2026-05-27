import logging

logger = logging.getLogger(__name__)

SAMPLE_PROCESSING_RATES = [
    {"toll_plaza_id": "TP001", "toll_plaza_name": "Amakthadu Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "January", "value": 98.5},
    {"toll_plaza_id": "TP002", "toll_plaza_name": "Dahisar Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "January", "value": 97.2},
    {"toll_plaza_id": "TP003", "toll_plaza_name": "Tambaram Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "January", "value": 99.1},
    {"toll_plaza_id": "TP004", "toll_plaza_name": "Noida Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "January", "value": 96.8},
    {"toll_plaza_id": "TP005", "toll_plaza_name": "Ahmedabad Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "January", "value": 98.9},
    {"toll_plaza_id": "TP001", "toll_plaza_name": "Amakthadu Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "February", "value": 97.8},
    {"toll_plaza_id": "TP002", "toll_plaza_name": "Dahisar Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "February", "value": 96.5},
    {"toll_plaza_id": "TP003", "toll_plaza_name": "Tambaram Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "February", "value": 98.7},
    {"toll_plaza_id": "TP004", "toll_plaza_name": "Noida Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "February", "value": 97.3},
    {"toll_plaza_id": "TP005", "toll_plaza_name": "Ahmedabad Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "February", "value": 99.0},
    {"toll_plaza_id": "TP001", "toll_plaza_name": "Amakthadu Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "March", "value": 98.2},
    {"toll_plaza_id": "TP002", "toll_plaza_name": "Dahisar Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "March", "value": 97.9},
    {"toll_plaza_id": "TP003", "toll_plaza_name": "Tambaram Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2025-26", "month": "March", "value": 99.3},
    {"toll_plaza_id": "TP004", "toll_plaza_name": "Noida Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2024-25", "month": "December", "value": 96.1},
    {"toll_plaza_id": "TP005", "toll_plaza_name": "Ahmedabad Toll Plaza", "toll_plaza_type": "National", "fiscal_year": "2024-25", "month": "December", "value": 98.6},
]

SAMPLE_UPTIME = [
    {"fiscal_year": "2025-26", "month": "January", "uptime": 99.95, "number_of_incidents": 2, "downtime": 45},
    {"fiscal_year": "2025-26", "month": "February", "uptime": 99.88, "number_of_incidents": 3, "downtime": 67},
    {"fiscal_year": "2025-26", "month": "March", "uptime": 99.92, "number_of_incidents": 1, "downtime": 23},
    {"fiscal_year": "2024-25", "month": "October", "uptime": 99.78, "number_of_incidents": 5, "downtime": 120},
    {"fiscal_year": "2024-25", "month": "November", "uptime": 99.85, "number_of_incidents": 4, "downtime": 89},
    {"fiscal_year": "2024-25", "month": "December", "uptime": 99.91, "number_of_incidents": 2, "downtime": 34},
    {"fiscal_year": "2024-25", "month": "January", "uptime": 99.93, "number_of_incidents": 1, "downtime": 15},
    {"fiscal_year": "2024-25", "month": "February", "uptime": 99.87, "number_of_incidents": 3, "downtime": 56},
    {"fiscal_year": "2024-25", "month": "March", "uptime": 99.96, "number_of_incidents": 1, "downtime": 12},
    {"fiscal_year": "2023-24", "month": "April", "uptime": 99.75, "number_of_incidents": 6, "downtime": 145},
    {"fiscal_year": "2023-24", "month": "May", "uptime": 99.82, "number_of_incidents": 4, "downtime": 78},
    {"fiscal_year": "2023-24", "month": "June", "uptime": 99.79, "number_of_incidents": 5, "downtime": 98},
]

SAMPLE_DISPUTES = [
    {"fiscal_year": "2025-26", "month": "January", "bank_name": "State Bank of India", "category": "Tag Not Read", "value": 12345},
    {"fiscal_year": "2025-26", "month": "January", "bank_name": "ICICI Bank", "category": "Double Charge", "value": 9876},
    {"fiscal_year": "2025-26", "month": "January", "bank_name": "HDFC Bank", "category": "Wrong Amount", "value": 7654},
    {"fiscal_year": "2025-26", "month": "February", "bank_name": "State Bank of India", "category": "Tag Not Read", "value": 11234},
    {"fiscal_year": "2025-26", "month": "February", "bank_name": "Axis Bank", "category": "Double Charge", "value": 8765},
    {"fiscal_year": "2025-26", "month": "February", "bank_name": "ICICI Bank", "category": "Wrong Amount", "value": 6543},
    {"fiscal_year": "2024-25", "month": "December", "bank_name": "State Bank of India", "category": "Tag Not Read", "value": 14567},
    {"fiscal_year": "2024-25", "month": "December", "bank_name": "HDFC Bank", "category": "Double Charge", "value": 10987},
    {"fiscal_year": "2024-25", "month": "November", "bank_name": "ICICI Bank", "category": "Tag Not Read", "value": 13210},
    {"fiscal_year": "2024-25", "month": "November", "bank_name": "Axis Bank", "category": "Wrong Amount", "value": 5432},
]


def fetch_csv(url):
    return []


def parse_processing_rates(rows):
    parsed = []
    for row in rows:
        try:
            parsed.append({
                "toll_plaza_id": row.get("toll_plaza_id", ""),
                "plaza_name": row.get("toll_plaza_name", ""),
                "plaza_type": row.get("toll_plaza_type", ""),
                "fiscal_year": row.get("fiscal_year", ""),
                "month": row.get("month", ""),
                "pct_within_2min": float(row.get("value", 0)),
            })
        except (ValueError, KeyError) as e:
            logger.warning("Skipping processing rate row: %s", e)
    return parsed


def parse_uptime(rows):
    parsed = []
    for row in rows:
        try:
            parsed.append({
                "fiscal_year": row.get("fiscal_year", ""),
                "month": row.get("month", ""),
                "uptime_pct": float(row.get("uptime", 0)),
                "incidents": int(row.get("number_of_incidents", 0)),
                "downtime_minutes": int(row.get("downtime", 0)),
            })
        except (ValueError, KeyError) as e:
            logger.warning("Skipping uptime row: %s", e)
    return parsed


def parse_disputes(rows):
    parsed = []
    for row in rows:
        try:
            parsed.append({
                "fiscal_year": row.get("fiscal_year", ""),
                "month": row.get("month", ""),
                "bank_name": row.get("bank_name", ""),
                "category": row.get("category", ""),
                "value": float(row.get("value", 0)),
            })
        except (ValueError, KeyError) as e:
            logger.warning("Skipping dispute row: %s", e)
    return parsed
