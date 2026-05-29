import json
import os
import random
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from insights.models import CongestionLog, RoadCondition, TollCollection, Trip
from insights.utils import load_config, invalidate_config_cache

VEHICLES = ["car", "bike", "bus", "truck", "ambulance"]

ROUTES = [
    # Hyderabad
    ("Hitech City, Hyderabad", "Gachibowli, Hyderabad", 17.4435, 78.3772, 17.4481, 78.3532),
    ("Jubilee Hills, Hyderabad", "Madhapur, Hyderabad", 17.4318, 78.4026, 17.4489, 78.3891),
    ("Hyderabad Airport", "HiTech City, Hyderabad", 17.2403, 78.4294, 17.4435, 78.3772),
    ("Secunderabad", "Ameerpet, Hyderabad", 17.4399, 78.4985, 17.4375, 78.4483),
    ("Kukatpally, Hyderabad", "Banjara Hills, Hyderabad", 17.4898, 78.4084, 17.4176, 78.4350),
    ("Miyapur, Hyderabad", "Kondapur, Hyderabad", 17.4974, 78.3673, 17.4699, 78.3669),
    ("LB Nagar, Hyderabad", "Dilsukhnagar, Hyderabad", 17.3476, 78.5527, 17.3699, 78.5257),
    ("Koti, Hyderabad", "Abids, Hyderabad", 17.3860, 78.4744, 17.3865, 78.4725),
    ("Patancheru, Hyderabad", "BHEL, Hyderabad", 17.5308, 78.2647, 17.4399, 78.2907),
    ("Uppal, Hyderabad", "Ramoji Film City", 17.4053, 78.5588, 17.3294, 78.6833),
    ("Nampally, Hyderabad", "Charminar", 17.3748, 78.4743, 17.3617, 78.4746),
    ("Himayatnagar, Hyderabad", "Somajiguda, Hyderabad", 17.3987, 78.4852, 17.4181, 78.4538),
    ("Toli Chowki, Hyderabad", "Mehdipatnam, Hyderabad", 17.3903, 78.4128, 17.3976, 78.4373),
    ("Shamshabad, Hyderabad", "Rajiv Gandhi International Airport", 17.2532, 78.4297, 17.2403, 78.4294),
    ("Begumpet, Hyderabad", "Paradise, Secunderabad", 17.4426, 78.4709, 17.4399, 78.4985),
    ("Alwal, Hyderabad", "Malkajgiri, Hyderabad", 17.5054, 78.5327, 17.4513, 78.5312),
    ("ECIL, Hyderabad", "Kushaiguda, Hyderabad", 17.4363, 78.5762, 17.4428, 78.5667),
    ("Boduppal, Hyderabad", "Peerzadiguda, Hyderabad", 17.4087, 78.5799, 17.4109, 78.5656),
    ("Narsingi, Hyderabad", "Manikonda, Hyderabad", 17.3731, 78.3452, 17.3971, 78.3814),
    ("Attapur, Hyderabad", "Rajendra Nagar, Hyderabad", 17.3678, 78.4171, 17.3403, 78.4044),
    # Delhi NCR
    ("Connaught Place, Delhi", "Gurgaon, Haryana", 28.6315, 77.2208, 28.4595, 77.0266),
    ("Dwarka, Delhi", "Noida, UP", 28.5920, 77.0394, 28.5355, 77.3910),
    ("Karol Bagh, Delhi", "India Gate, Delhi", 28.6539, 77.1905, 28.6129, 77.2295),
    ("Saket, Delhi", "Rohini, Delhi", 28.5264, 77.2214, 28.7376, 77.1471),
    ("Laxmi Nagar, Delhi", "Chandni Chowk, Delhi", 28.6329, 77.2822, 28.6562, 77.2302),
    # Mumbai
    ("Andheri West, Mumbai", "Bandra Kurla Complex, Mumbai", 19.1360, 72.8310, 19.0689, 72.8700),
    ("Dadar, Mumbai", "Navi Mumbai", 19.0178, 72.8478, 19.0330, 73.0297),
    ("Borivali, Mumbai", "Churchgate, Mumbai", 19.2263, 72.8578, 18.9322, 72.8266),
    ("Thane West", "Ghatkopar, Mumbai", 19.2180, 72.9785, 19.0850, 72.9080),
    ("Colaba, Mumbai", "Lower Parel, Mumbai", 18.9067, 72.8113, 18.9930, 72.8258),
    # Bangalore
    ("MG Road, Bangalore", "Whitefield, Bangalore", 12.9716, 77.5946, 12.9698, 77.7500),
    ("Electronic City, Bangalore", "Hebbal, Bangalore", 12.8399, 77.6770, 13.0358, 77.5970),
    ("Koramangala, Bangalore", "Indiranagar, Bangalore", 12.9350, 77.6270, 12.9784, 77.6408),
    ("Jayanagar, Bangalore", "Yelahanka, Bangalore", 12.9296, 77.5826, 13.1007, 77.5963),
    ("Majestic, Bangalore", "Marathahalli, Bangalore", 12.9767, 77.5713, 12.9591, 77.7000),
    # Chennai
    ("T Nagar, Chennai", "OMR, Chennai", 13.0408, 80.2350, 12.9516, 80.2413),
    ("Anna Nagar, Chennai", "Guindy, Chennai", 13.0850, 80.2100, 13.0067, 80.2206),
    ("Velachery, Chennai", "Tambaram, Chennai", 12.9800, 80.2180, 12.9249, 80.1000),
    ("Adyar, Chennai", "Chennai Central", 13.0025, 80.2571, 13.0827, 80.2750),
    # Kolkata
    ("Howrah, Kolkata", "Salt Lake, Kolkata", 22.5854, 88.3150, 22.5848, 88.4160),
    ("Park Street, Kolkata", "Dum Dum, Kolkata", 22.5580, 88.3518, 22.6146, 88.4308),
    ("Sealdah, Kolkata", "New Town, Kolkata", 22.5682, 88.3680, 22.5860, 88.4680),
    ("Ballygunge, Kolkata", "Barasat, Kolkata", 22.5150, 88.3630, 22.7163, 88.4916),
    # Pune
    ("Shivajinagar, Pune", "Hinjewadi, Pune", 18.5290, 73.8460, 18.5893, 73.7270),
    ("Koregaon Park, Pune", "Kharadi, Pune", 18.5360, 73.8970, 18.5500, 73.9400),
    ("Swargate, Pune", "Pimpri, Pune", 18.4970, 73.8520, 18.6298, 73.8057),
    # Ahmedabad
    ("SG Highway, Ahmedabad", "Gandhinagar", 23.0890, 72.5860, 23.2156, 72.6369),
    ("Maninagar, Ahmedabad", "Bopal, Ahmedabad", 22.9970, 72.6060, 23.0340, 72.4640),
    ("Vadaj, Ahmedabad", "Satellite, Ahmedabad", 23.0580, 72.5820, 23.0190, 72.5130),
    # Jaipur
    ("Mansarovar, Jaipur", "MI Road, Jaipur", 26.8560, 75.7650, 26.9168, 75.8230),
    ("Sitapura, Jaipur", "WTP, Jaipur", 26.7900, 75.8800, 26.8970, 75.7590),
    # Lucknow
    ("Gomti Nagar, Lucknow", "Hazratganj, Lucknow", 26.8420, 81.0000, 26.8510, 80.9410),
    ("Aliganj, Lucknow", "Charbagh, Lucknow", 26.8880, 80.9290, 26.8280, 80.9210),
    # Chandigarh
    ("Sector 17, Chandigarh", "Panchkula, Haryana", 30.7570, 76.7840, 30.6940, 76.8510),
    ("Mohali", "Sector 35, Chandigarh", 30.7050, 76.7220, 30.7400, 76.7670),
    # Bhopal
    ("MP Nagar, Bhopal", "Habibganj, Bhopal", 23.2320, 77.4380, 23.2440, 77.4540),
    ("Lal Ghati, Bhopal", "Kolar Road, Bhopal", 23.2640, 77.4140, 23.1980, 77.4100),
    # Surat
    ("City Light, Surat", "Udhana, Surat", 21.1890, 72.8180, 21.1690, 72.8540),
    ("Adajan, Surat", "Varachha, Surat", 21.2140, 72.8000, 21.2040, 72.8720),
    # Indore
    ("Vijay Nagar, Indore", "Rajwada, Indore", 22.7520, 75.8940, 22.7180, 75.8580),
    ("Scheme 140, Indore", "Airport, Indore", 22.7400, 75.8730, 22.7200, 75.8020),
    # Nagpur
    ("Sitabuldi, Nagpur", "Wardha Road, Nagpur", 21.1480, 79.0870, 21.1300, 79.0880),
    ("Dharampeth, Nagpur", "Hingna Road, Nagpur", 21.1420, 79.1460, 21.1140, 79.0580),
    # Patna
    ("Boring Road, Patna", "Patna Junction", 25.6090, 85.1080, 25.6150, 85.1370),
    ("Kankarbagh, Patna", "Danapur, Patna", 25.5900, 85.1500, 25.6200, 85.0490),
    # Bhubaneswar
    ("Kalinga Nagar, Bhubaneswar", "Master Canteen, Bhubaneswar", 20.3140, 85.8180, 20.2960, 85.8310),
    ("Bhubaneswar Airport", "Nandankanan Road", 20.2930, 85.8200, 20.3450, 85.8320),
    # Kochi
    ("MG Road, Kochi", "Edappally, Kochi", 9.9650, 76.2850, 10.0100, 76.3060),
    ("Fort Kochi", "Vytilla, Kochi", 9.9650, 76.2420, 9.9730, 76.3140),
    # Coimbatore
    ("Gandhipuram, Coimbatore", "Peelamedu, Coimbatore", 11.0150, 76.9740, 11.0250, 76.9960),
    ("RS Puram, Coimbatore", "Sitra, Coimbatore", 11.0030, 76.9560, 11.0140, 77.0300),
    # Visakhapatnam
    ("Dabagardens, Vizag", "Madhurawada, Vizag", 17.7180, 83.3050, 17.7650, 83.3400),
    ("Gajuwaka, Vizag", "Rushikonda, Vizag", 17.6990, 83.2170, 17.7780, 83.3800),
    # Varanasi
    ("Assi Ghat, Varanasi", "Cantonment, Varanasi", 25.2850, 82.9990, 25.3310, 82.9960),
    ("Lanka, Varanasi", "Sigra, Varanasi", 25.2950, 82.9930, 25.3150, 82.9760),
    # Guwahati
    ("Dispur, Guwahati", "Paltan Bazar, Guwahati", 26.1400, 91.7900, 26.1820, 91.7510),
    ("Guwahati Airport", "Pan Bazar, Guwahati", 26.1060, 91.5860, 26.1830, 91.7500),
    # Ranchi
    ("Main Road, Ranchi", "Doranda, Ranchi", 23.3580, 85.3340, 23.3730, 85.3190),
    ("Hatia, Ranchi", "Kanke, Ranchi", 23.3210, 85.3180, 23.3870, 85.3270),
    # Raipur
    ("Telibandha, Raipur", "Pandri, Raipur", 21.2460, 81.6480, 21.2410, 81.6340),
    ("Raipur Railway Station", "Naya Raipur", 21.2190, 81.6420, 21.1630, 81.7750),
    # Dehradun
    ("ISBT Dehradun", "Clock Tower, Dehradun", 30.3290, 78.0340, 30.3150, 78.0450),
    ("Rajpur Road, Dehradun", "Prem Nagar, Dehradun", 30.3290, 78.0670, 30.3500, 78.0000),
]

CONGESTION_LOCATIONS = [
    # Hyderabad
    ("Junction 1 - Hitech City", 17.4435, 78.3772),
    ("Junction 2 - Gachibowli", 17.4481, 78.3532),
    ("Junction 3 - Madhapur", 17.4489, 78.3891),
    ("Junction 4 - Ameerpet", 17.4375, 78.4483),
    ("Junction 5 - Kukatpally", 17.4898, 78.4084),
    ("Junction 6 - LB Nagar", 17.3476, 78.5527),
    ("Junction 7 - Dilsukhnagar", 17.3699, 78.5257),
    ("Junction 8 - Charminar", 17.3617, 78.4746),
    # Delhi NCR
    ("ITO Junction, Delhi", 28.6280, 77.2430),
    ("Dhaula Kuan, Delhi", 28.5880, 77.1700),
    ("AIIMS Chowk, Delhi", 28.5670, 77.2100),
    ("Noida Sector 18, UP", 28.5690, 77.3250),
    ("Gurgaon MG Road, Haryana", 28.4790, 77.0910),
    # Mumbai
    ("Bandra Worli Sea Link", 19.0450, 72.8150),
    ("Western Express Highway, Mumbai", 19.1000, 72.8570),
    ("Sion Circle, Mumbai", 19.0500, 72.8640),
    ("Andheri-Kurla Road, Mumbai", 19.1170, 72.8690),
    ("Vashi Junction, Navi Mumbai", 19.0750, 72.9930),
    # Bangalore
    ("Silk Board Junction, Bangalore", 12.9170, 77.6220),
    ("KR Puram, Bangalore", 12.9980, 77.7030),
    ("Majestic Bus Stand, Bangalore", 12.9770, 77.5710),
    ("Hebbal Flyover, Bangalore", 13.0360, 77.5960),
    ("Marathahalli Bridge, Bangalore", 12.9560, 77.7010),
    # Chennai
    ("Kathipara Junction, Chennai", 13.0050, 80.2100),
    ("Padi Junction, Chennai", 13.1000, 80.1930),
    ("Thoraipakkam Junction, Chennai", 12.9450, 80.2230),
    ("Guindy, Chennai", 13.0070, 80.2210),
    # Kolkata
    ("Howrah Bridge Approach", 22.5850, 88.3320),
    ("Esplanade, Kolkata", 22.5660, 88.3490),
    ("Ballygunge Phari, Kolkata", 22.5170, 88.3640),
    ("Ultadanga, Kolkata", 22.5910, 88.3960),
    # Pune
    ("Shivajinagar, Pune", 18.5300, 73.8450),
    ("Katraj Chowk, Pune", 18.4550, 73.8610),
    ("Bund Garden, Pune", 18.5380, 73.8760),
    # Ahmedabad
    ("Nehru Bridge, Ahmedabad", 23.0300, 72.5740),
    ("Drive-in Road, Ahmedabad", 23.0430, 72.5400),
    ("Shahibaug, Ahmedabad", 23.0650, 72.5990),
    # Other cities
    ("Gomti Nagar, Lucknow", 26.8420, 81.0000),
    ("MI Road, Jaipur", 26.9170, 75.8230),
    ("Sector 17, Chandigarh", 30.7570, 76.7840),
    ("MP Nagar, Bhopal", 23.2320, 77.4380),
    ("MG Road, Kochi", 9.9650, 76.2850),
    ("Gandhipuram, Coimbatore", 11.0150, 76.9740),
    ("Dabagardens, Visakhapatnam", 17.7180, 83.3050),
    ("Assi Ghat, Varanasi", 25.2850, 82.9990),
    ("Paltan Bazar, Guwahati", 26.1820, 91.7510),
    ("Main Road, Ranchi", 23.3580, 85.3340),
    ("Pandri, Raipur", 21.2410, 81.6340),
    ("Clock Tower, Dehradun", 30.3150, 78.0450),
]

ROAD_CONDITIONS_DATA = [
    # Hyderabad
    ("Hitech City Road", 17.4440, 78.3775, "pothole", "medium"),
    ("Gachibowli Flyover", 17.4475, 78.3540, "under_construction", "high"),
    ("Madhapur Main Road", 17.4495, 78.3885, "fair", "low"),
    ("Ameerpet Junction", 17.4378, 78.4480, "accident", "high"),
    ("Kukatpally Road", 17.4902, 78.4080, "poor", "medium"),
    ("LB Nagar Underpass", 17.3470, 78.5520, "flooding", "critical"),
    ("Dilsukhnagar Road", 17.3705, 78.5250, "pothole", "medium"),
    ("Charminar Approach", 17.3620, 78.4740, "good", "low"),
    # Delhi NCR
    ("Ring Road, Delhi", 28.6100, 77.2300, "pothole", "medium"),
    ("Bandra Road, Gurgaon", 28.4800, 77.0900, "under_construction", "high"),
    ("Noida Expressway", 28.5700, 77.3200, "poor", "medium"),
    ("Dhaula Kuan Underpass", 28.5900, 77.1680, "flooding", "critical"),
    ("Mukarba Chowk, Delhi", 28.7000, 77.1550, "accident", "high"),
    # Mumbai
    ("Western Express Highway", 19.1000, 72.8570, "pothole", "medium"),
    ("Bandra Kurla Complex Road", 19.0700, 72.8700, "fair", "low"),
    ("Sion-Panvel Highway", 19.0500, 72.8650, "under_construction", "high"),
    ("Link Road, Andheri", 19.1350, 72.8300, "flooding", "medium"),
    ("Eastern Express Highway", 19.0800, 72.8800, "accident", "high"),
    # Bangalore
    ("Silk Board Junction Road", 12.9170, 77.6220, "pothole", "critical"),
    ("Old Airport Road", 12.9600, 77.6600, "poor", "medium"),
    ("NICE Road Entry", 12.8800, 77.5600, "under_construction", "medium"),
    ("KR Puram Bridge Road", 12.9980, 77.7030, "fair", "low"),
    ("Mysore Road, Bangalore", 12.9400, 77.5300, "pothole", "medium"),
    # Chennai
    ("OMR Road, Chennai", 12.9500, 80.2400, "under_construction", "high"),
    ("Mount Road, Chennai", 13.0600, 80.2600, "pothole", "medium"),
    ("Chennai Bypass", 13.0800, 80.2000, "fair", "low"),
    ("Old Mahabalipuram Road", 12.9300, 80.2300, "poor", "medium"),
    # Kolkata
    ("Vidyasagar Setu Approach", 22.5500, 88.3200, "accident", "high"),
    ("EM Bypass, Kolkata", 22.5300, 88.4000, "pothole", "medium"),
    ("Ballygunge Circular Road", 22.5200, 88.3650, "under_construction", "low"),
    # Pune
    ("Katraj Bypass", 18.4550, 73.8600, "pothole", "medium"),
    ("JM Road, Pune", 18.5300, 73.8620, "good", "low"),
    ("Ahmednagar Road, Pune", 18.5500, 73.9000, "poor", "high"),
    # Ahmedabad
    ("SG Highway, Ahmedabad", 23.0880, 72.5850, "under_construction", "medium"),
    ("Ashram Road, Ahmedabad", 23.0400, 72.5720, "pothole", "low"),
    ("Narol Circle, Ahmedabad", 22.9700, 72.6000, "accident", "high"),
    # Other cities
    ("MI Road, Jaipur", 26.9160, 75.8220, "pothole", "medium"),
    ("Hazratganj, Lucknow", 26.8510, 80.9410, "fair", "low"),
    ("Sector 17, Chandigarh", 30.7570, 76.7840, "good", "low"),
    ("MP Nagar, Bhopal", 23.2320, 77.4380, "pothole", "medium"),
    ("Vijay Nagar, Indore", 22.7520, 75.8930, "under_construction", "high"),
    ("Sitabuldi, Nagpur", 21.1480, 79.0870, "poor", "medium"),
    ("MG Road, Kochi", 9.9650, 76.2850, "pothole", "medium"),
    ("Gandhipuram, Coimbatore", 11.0150, 76.9740, "accident", "high"),
    ("Rushikonda Road, Vizag", 17.7780, 83.3800, "fair", "low"),
    ("Lanka, Varanasi", 25.2950, 82.9930, "poor", "medium"),
    ("GS Road, Guwahati", 26.1750, 91.7500, "pothole", "high"),
    ("Kanke Road, Ranchi", 23.3870, 85.3270, "under_construction", "medium"),
    ("Telibandha, Raipur", 21.2460, 81.6480, "good", "low"),
    ("Rajpur Road, Dehradun", 30.3300, 78.0670, "pothole", "medium"),
]


def _build_route_geometry(olng, olat, dlng, dlat):
    mid_lat = (olat + dlat) / 2
    mid_lng = (olng + dlng) / 2
    return {
        "type": "LineString",
        "coordinates": [
            [olng, olat],
            [mid_lng + random.uniform(-0.02, 0.02), mid_lat + random.uniform(-0.02, 0.02)],
            [dlng, dlat],
        ],
    }


def _compute_toll(distance_km, vehicle):
    config = load_config()
    tc = config["toll"]
    if distance_km <= tc["decision_threshold_km"]:
        base_toll = tc["slabs"][-1]["rate"]
        for slab in tc["slabs"]:
            if slab["max_km"] is None or distance_km <= slab["max_km"]:
                base_toll = slab["rate"]
                break
        model = "slab"
    else:
        base_toll = distance_km * tc["dynamic_rate_per_km"]
        model = "dynamic"
    multiplier = tc["vehicle_multipliers"].get(vehicle, 1.0)
    return round(base_toll * multiplier, 2), model, base_toll, multiplier


class Command(BaseCommand):
    help = "Seed database with sample trips, congestion logs, and road conditions"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Delete existing data before seeding")

    def handle(self, *args, **options):
        invalidate_config_cache()

        if options["force"]:
            self.stdout.write("Clearing existing data...")
            RoadCondition.objects.all().delete()
            CongestionLog.objects.all().delete()
            TollCollection.objects.all().delete()
            Trip.objects.all().delete()

        admin_user = User.objects.filter(username="admin").first()
        if not admin_user:
            admin_user = User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write("Created admin user")

        demo_user = User.objects.filter(username="user").first()
        if not demo_user:
            demo_user = User.objects.create_user("user", "user@example.com", "user1234")
            self.stdout.write("Created demo user")

        if Trip.objects.exists() and not options["force"]:
            self.stdout.write("Data already exists, skipping seed. Use --force to re-seed.")
            return

        today = timezone.now().date()

        for i, (origin_name, dest_name, olat, olng, dlat, dlng) in enumerate(ROUTES):
            user = admin_user if i < 5 else demo_user
            offset_days = random.randint(0, 29)
            created = timezone.make_aware(datetime.combine(
                today - timedelta(days=offset_days),
                datetime.min.time().replace(hour=random.randint(6, 22), minute=random.randint(0, 59)),
            ))
            vehicle = random.choice(VEHICLES)
            distance_km = round(random.uniform(3, 25), 1)
            toll, model, base_toll, multiplier = _compute_toll(distance_km, vehicle)

            trip = Trip.objects.create(
                user=user,
                origin_name=origin_name,
                dest_name=dest_name,
                origin_lat=olat,
                origin_lng=olng,
                dest_lat=dlat,
                dest_lng=dlng,
                distance_km=distance_km,
                duration_sec=random.randint(300, 1800),
                route_geometry=_build_route_geometry(olng, olat, dlng, dlat),
                vehicle_type=vehicle,
                toll_amount=toll,
                pricing_model=model,
                congestion_level=random.choice(["light", "moderate", "heavy", "congested"]),
                created_at=created,
            )

            if toll and multiplier > 0:
                TollCollection.objects.create(
                    trip=trip,
                    base_toll=round(base_toll, 2),
                    multiplier=multiplier,
                    total_toll=toll,
                    pricing_model=model,
                )

        self.stdout.write(f"Created {len(ROUTES)} sample trips")

        for name, lat, lng in CONGESTION_LOCATIONS:
            for _ in range(random.randint(3, 8)):
                created = timezone.make_aware(datetime.combine(
                    today - timedelta(days=random.randint(0, 29)),
                    datetime.min.time().replace(hour=random.randint(7, 21)),
                ))
                CongestionLog.objects.create(
                    location_name=name,
                    lat=lat + random.uniform(-0.002, 0.002),
                    lng=lng + random.uniform(-0.002, 0.002),
                    level=round(random.uniform(0.7, 2.5), 2),
                    source="query",
                    created_at=created,
                )

        self.stdout.write("Created congestion logs")

        for name, lat, lng, ctype, severity in ROAD_CONDITIONS_DATA:
            status = random.choices(["reported", "verified", "resolved"], weights=[3, 3, 1])[0]
            resolved_at = timezone.now() - timedelta(days=random.randint(1, 5)) if status == "resolved" else None
            RoadCondition.objects.create(
                road_name=name,
                lat=lat,
                lng=lng,
                condition_type=ctype,
                severity=severity,
                description=f"{ctype.replace('_', ' ').title()} on {name}",
                reported_by=random.choice([admin_user, demo_user, None]),
                report_count=random.randint(1, 5),
                status=status,
                resolved_at=resolved_at,
            )

        self.stdout.write(f"Created {len(ROAD_CONDITIONS_DATA)} road conditions")
        self.stdout.write(self.style.SUCCESS("Seed complete"))
