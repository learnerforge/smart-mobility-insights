import logging

logger = logging.getLogger(__name__)

SAMPLE_ROAD_LENGTHS = [
    {"year": 2023, "road_category": "National Highways", "road_property": "Total", "value": 145240, "unit": "Kilometer"},
    {"year": 2023, "road_category": "National Highways", "road_property": "Surfaced", "value": 145240, "unit": "Kilometer"},
    {"year": 2023, "road_category": "State Highways", "road_property": "Total", "value": 186528, "unit": "Kilometer"},
    {"year": 2023, "road_category": "State Highways", "road_property": "Surfaced", "value": 175000, "unit": "Kilometer"},
    {"year": 2023, "road_category": "District Roads", "road_property": "Total", "value": 634437, "unit": "Kilometer"},
    {"year": 2023, "road_category": "District Roads", "road_property": "Surfaced", "value": 450000, "unit": "Kilometer"},
    {"year": 2023, "road_category": "Rural Roads", "road_property": "Total", "value": 3890552, "unit": "Kilometer"},
    {"year": 2023, "road_category": "Rural Roads", "road_property": "Surfaced", "value": 2100000, "unit": "Kilometer"},
    {"year": 2023, "road_category": "Urban Roads", "road_property": "Total", "value": 523000, "unit": "Kilometer"},
    {"year": 2023, "road_category": "Urban Roads", "road_property": "Surfaced", "value": 500000, "unit": "Kilometer"},
    {"year": 2023, "road_category": "Project Roads", "road_property": "Total", "value": 387660, "unit": "Kilometer"},
    {"year": 2023, "road_category": "Project Roads", "road_property": "Surfaced", "value": 375000, "unit": "Kilometer"},
    {"year": 2022, "road_category": "National Highways", "road_property": "Total", "value": 140995, "unit": "Kilometer"},
    {"year": 2022, "road_category": "National Highways", "road_property": "Surfaced", "value": 140995, "unit": "Kilometer"},
    {"year": 2022, "road_category": "State Highways", "road_property": "Total", "value": 183432, "unit": "Kilometer"},
    {"year": 2022, "road_category": "State Highways", "road_property": "Surfaced", "value": 172000, "unit": "Kilometer"},
    {"year": 2022, "road_category": "District Roads", "road_property": "Total", "value": 625345, "unit": "Kilometer"},
    {"year": 2022, "road_category": "District Roads", "road_property": "Surfaced", "value": 440000, "unit": "Kilometer"},
    {"year": 2022, "road_category": "Rural Roads", "road_property": "Total", "value": 3834567, "unit": "Kilometer"},
    {"year": 2022, "road_category": "Rural Roads", "road_property": "Surfaced", "value": 2000000, "unit": "Kilometer"},
    {"year": 2022, "road_category": "Urban Roads", "road_property": "Total", "value": 510000, "unit": "Kilometer"},
    {"year": 2022, "road_category": "Urban Roads", "road_property": "Surfaced", "value": 490000, "unit": "Kilometer"},
    {"year": 2022, "road_category": "Project Roads", "road_property": "Total", "value": 380000, "unit": "Kilometer"},
    {"year": 2022, "road_category": "Project Roads", "road_property": "Surfaced", "value": 368000, "unit": "Kilometer"},
    {"year": 2021, "road_category": "National Highways", "road_property": "Total", "value": 136440, "unit": "Kilometer"},
    {"year": 2021, "road_category": "National Highways", "road_property": "Surfaced", "value": 136440, "unit": "Kilometer"},
    {"year": 2021, "road_category": "State Highways", "road_property": "Total", "value": 180234, "unit": "Kilometer"},
    {"year": 2021, "road_category": "State Highways", "road_property": "Surfaced", "value": 169000, "unit": "Kilometer"},
    {"year": 2021, "road_category": "District Roads", "road_property": "Total", "value": 615000, "unit": "Kilometer"},
    {"year": 2021, "road_category": "District Roads", "road_property": "Surfaced", "value": 432000, "unit": "Kilometer"},
    {"year": 2021, "road_category": "Rural Roads", "road_property": "Total", "value": 3780000, "unit": "Kilometer"},
    {"year": 2021, "road_category": "Rural Roads", "road_property": "Surfaced", "value": 1950000, "unit": "Kilometer"},
    {"year": 2021, "road_category": "Urban Roads", "road_property": "Total", "value": 498000, "unit": "Kilometer"},
    {"year": 2021, "road_category": "Urban Roads", "road_property": "Surfaced", "value": 478000, "unit": "Kilometer"},
    {"year": 2021, "road_category": "Project Roads", "road_property": "Total", "value": 372000, "unit": "Kilometer"},
    {"year": 2021, "road_category": "Project Roads", "road_property": "Surfaced", "value": 360000, "unit": "Kilometer"},
]


def fetch_road_length_csv():
    return SAMPLE_ROAD_LENGTHS


def parse_road_lengths(rows):
    parsed = []
    for row in rows:
        try:
            parsed.append({
                "year": row["year"],
                "road_category": row["road_category"],
                "road_property": row["road_property"],
                "value": row["value"],
                "unit": row.get("unit", "value in Kilometer"),
            })
        except (ValueError, KeyError) as e:
            logger.warning("Skipping road length row: %s", e)
    return parsed


def fetch_nh_length_csv():
    return []
