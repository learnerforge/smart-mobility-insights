import logging

logger = logging.getLogger(__name__)

SAMPLE_VIOLATIONS = [
    {"year": 2022, "state": "Tamil Nadu", "city": "Chennai", "type_of_traffic_violation": "Overspeeding", "category": "Killed", "value": 456},
    {"year": 2022, "state": "Tamil Nadu", "city": "Chennai", "type_of_traffic_violation": "Overspeeding", "category": "Injured", "value": 1234},
    {"year": 2022, "state": "Maharashtra", "city": "Mumbai", "type_of_traffic_violation": "Drunk Driving", "category": "Killed", "value": 234},
    {"year": 2022, "state": "Maharashtra", "city": "Mumbai", "type_of_traffic_violation": "Drunk Driving", "category": "Injured", "value": 678},
    {"year": 2022, "state": "Uttar Pradesh", "city": "Lucknow", "type_of_traffic_violation": "Red Light Jumping", "category": "Killed", "value": 345},
    {"year": 2022, "state": "Uttar Pradesh", "city": "Lucknow", "type_of_traffic_violation": "Red Light Jumping", "category": "Injured", "value": 890},
    {"year": 2022, "state": "Karnataka", "city": "Bengaluru", "type_of_traffic_violation": "Lane Cutting", "category": "Killed", "value": 123},
    {"year": 2022, "state": "Karnataka", "city": "Bengaluru", "type_of_traffic_violation": "Lane Cutting", "category": "Injured", "value": 567},
    {"year": 2022, "state": "Delhi", "city": "Delhi", "type_of_traffic_violation": "Overspeeding", "category": "Killed", "value": 789},
    {"year": 2022, "state": "Delhi", "city": "Delhi", "type_of_traffic_violation": "Overspeeding", "category": "Injured", "value": 2345},
    {"year": 2023, "state": "Tamil Nadu", "city": "Chennai", "type_of_traffic_violation": "Overspeeding", "category": "Killed", "value": 432},
    {"year": 2023, "state": "Maharashtra", "city": "Mumbai", "type_of_traffic_violation": "Drunk Driving", "category": "Killed", "value": 210},
    {"year": 2023, "state": "Uttar Pradesh", "city": "Lucknow", "type_of_traffic_violation": "Red Light Jumping", "category": "Killed", "value": 321},
    {"year": 2023, "state": "Karnataka", "city": "Bengaluru", "type_of_traffic_violation": "Lane Cutting", "category": "Injured", "value": 543},
    {"year": 2023, "state": "Delhi", "city": "Delhi", "type_of_traffic_violation": "Overspeeding", "category": "Killed", "value": 756},
    {"year": 2023, "state": "Gujarat", "city": "Ahmedabad", "type_of_traffic_violation": "Drunk Driving", "category": "Killed", "value": 189},
    {"year": 2023, "state": "Rajasthan", "city": "Jaipur", "type_of_traffic_violation": "Overspeeding", "category": "Killed", "value": 267},
    {"year": 2023, "state": "West Bengal", "city": "Kolkata", "type_of_traffic_violation": "Red Light Jumping", "category": "Injured", "value": 678},
    {"year": 2023, "state": "Telangana", "city": "Hyderabad", "type_of_traffic_violation": "Overspeeding", "category": "Killed", "value": 345},
    {"year": 2024, "state": "Maharashtra", "city": "Mumbai", "type_of_traffic_violation": "Overspeeding", "category": "Killed", "value": 198},
    {"year": 2024, "state": "Tamil Nadu", "city": "Chennai", "type_of_traffic_violation": "Drunk Driving", "category": "Killed", "value": 167},
    {"year": 2024, "state": "Delhi", "city": "Delhi", "type_of_traffic_violation": "Overspeeding", "category": "Killed", "value": 678},
    {"year": 2024, "state": "Karnataka", "city": "Bengaluru", "type_of_traffic_violation": "Lane Cutting", "category": "Injured", "value": 432},
    {"year": 2024, "state": "Uttar Pradesh", "city": "Lucknow", "type_of_traffic_violation": "Red Light Jumping", "category": "Killed", "value": 290},
]

SAMPLE_COLLISIONS = [
    {"Year": 2022, "Type_of_collision": "Head On", "Accidents": 12456, "Killed": 5234, "Injured": 9876},
    {"Year": 2022, "Type_of_collision": "Rear End", "Accidents": 23456, "Killed": 1234, "Injured": 18765},
    {"Year": 2022, "Type_of_collision": "Side Swipe", "Accidents": 34567, "Killed": 2345, "Injured": 23456},
    {"Year": 2022, "Type_of_collision": "Run Off Road", "Accidents": 45678, "Killed": 6789, "Injured": 34567},
    {"Year": 2022, "Type_of_collision": "Hit Pedestrian", "Accidents": 15678, "Killed": 4567, "Injured": 11234},
    {"Year": 2023, "Type_of_collision": "Head On", "Accidents": 11890, "Killed": 4987, "Injured": 9432},
    {"Year": 2023, "Type_of_collision": "Rear End", "Accidents": 22345, "Killed": 1156, "Injured": 17890},
    {"Year": 2023, "Type_of_collision": "Side Swipe", "Accidents": 33456, "Killed": 2234, "Injured": 22345},
    {"Year": 2023, "Type_of_collision": "Run Off Road", "Accidents": 44567, "Killed": 6543, "Injured": 33456},
    {"Year": 2023, "Type_of_collision": "Hit Pedestrian", "Accidents": 14901, "Killed": 4321, "Injured": 10678},
    {"Year": 2024, "Type_of_collision": "Head On", "Accidents": 11234, "Killed": 4765, "Injured": 9012},
    {"Year": 2024, "Type_of_collision": "Rear End", "Accidents": 21234, "Killed": 1098, "Injured": 17012},
    {"Year": 2024, "Type_of_collision": "Side Swipe", "Accidents": 32345, "Killed": 2123, "Injured": 21234},
    {"Year": 2024, "Type_of_collision": "Run Off Road", "Accidents": 43456, "Killed": 6321, "Injured": 32345},
    {"Year": 2024, "Type_of_collision": "Hit Pedestrian", "Accidents": 14123, "Killed": 4109, "Injured": 10123},
]


def fetch_violations_csv():
    return SAMPLE_VIOLATIONS


def parse_violations(rows):
    parsed = []
    for row in rows:
        try:
            parsed.append({
                "year": row["year"],
                "state": row["state"],
                "city": row.get("city", ""),
                "type_of_traffic_violation": row.get("type_of_traffic_violation", ""),
                "category": row["category"],
                "value": row["value"],
            })
        except (ValueError, KeyError) as e:
            logger.warning("Skipping violation row: %s", e)
    return parsed


def fetch_collision_csv():
    return SAMPLE_COLLISIONS


def parse_collisions(rows):
    parsed = []
    for row in rows:
        try:
            parsed.append({
                "year": row["Year"],
                "collision_type": row.get("Type_of_collision", ""),
                "accidents": row.get("Accidents"),
                "killed": row.get("Killed"),
                "injured": row.get("Injured"),
            })
        except (ValueError, KeyError) as e:
            logger.warning("Skipping collision row: %s", e)
    return parsed


SAMPLE_ROAD_USERS = [
    {"year": 2022, "road_user_type": "Pedestrian", "killed": 4567},
    {"year": 2022, "road_user_type": "Cyclist", "killed": 1234},
    {"year": 2022, "road_user_type": "Two Wheeler", "killed": 12345},
    {"year": 2022, "road_user_type": "Car", "killed": 6789},
    {"year": 2022, "road_user_type": "Truck", "killed": 3456},
    {"year": 2022, "road_user_type": "Bus", "killed": 1234},
    {"year": 2023, "road_user_type": "Pedestrian", "killed": 4321},
    {"year": 2023, "road_user_type": "Cyclist", "killed": 1156},
    {"year": 2023, "road_user_type": "Two Wheeler", "killed": 11987},
    {"year": 2023, "road_user_type": "Car", "killed": 6543},
    {"year": 2023, "road_user_type": "Truck", "killed": 3321},
    {"year": 2023, "road_user_type": "Bus", "killed": 1189},
    {"year": 2024, "road_user_type": "Pedestrian", "killed": 4109},
    {"year": 2024, "road_user_type": "Cyclist", "killed": 1098},
    {"year": 2024, "road_user_type": "Two Wheeler", "killed": 11456},
    {"year": 2024, "road_user_type": "Car", "killed": 6321},
    {"year": 2024, "road_user_type": "Truck", "killed": 3198},
    {"year": 2024, "road_user_type": "Bus", "killed": 1123},
]


def fetch_road_users_csv():
    return SAMPLE_ROAD_USERS


def parse_road_users(rows):
    parsed = []
    for row in rows:
        try:
            parsed.append({
                "year": row["year"],
                "road_user_type": row["road_user_type"],
                "killed": row.get("killed"),
            })
        except (ValueError, KeyError) as e:
            logger.warning("Skipping road user row: %s", e)
    return parsed
