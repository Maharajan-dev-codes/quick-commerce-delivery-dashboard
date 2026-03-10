import mysql.connector
import pandas as pd
import random
from datetime import datetime, timedelta

# ------------------ MYSQL CONNECTION ------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_password",
    database="quick_commerce_analysis_v2"
)
cursor = conn.cursor()
print("Connected to MySQL")

# ------------------ LOAD MASTER DATA ------------------
zones_df = pd.read_sql("SELECT zone_id FROM zones", conn)
riders_df = pd.read_sql("SELECT rider_id FROM riders", conn)

zone_ids = zones_df['zone_id'].tolist()
rider_ids = riders_df['rider_id'].tolist()

# ------------------ TIME SLOT DISTRIBUTION ------------------
# (1–5 AM very low demand)
time_slots = [
    (1, 5, 0.02),     # deep night (very low)
    (5, 8, 0.08),
    (8, 11, 0.15),
    (11, 14, 0.25),   # lunch peak
    (14, 17, 0.12),
    (17, 21, 0.28),   # evening peak
    (21, 24, 0.10)
]

def generate_order_time(base_date):
    slot = random.choices(time_slots, weights=[s[2] for s in time_slots])[0]
    hour = random.randint(slot[0], slot[1] - 1)
    minute = random.randint(0, 59)
    return base_date.replace(hour=hour, minute=minute, second=0)

# ------------------ SAFE ORDER ID START ------------------
cursor.execute("SELECT MAX(order_id) FROM orders")
last_id = cursor.fetchone()[0]
order_id = 1000 if last_id is None else last_id + 1

# ------------------ GENERATION CONFIG ------------------
days = 30
base_orders_per_day = 420
start_date = datetime(2025, 1, 1)

# ------------------ DATA GENERATION ------------------
for d in range(days):
    base_date = start_date + timedelta(days=d)

    for _ in range(base_orders_per_day):
        order_time = generate_order_time(base_date)

        # 🔹 Skip most orders during 1–5 AM
        if 1 <= order_time.hour < 5:
            if random.random() > 0.15:   # 85% dropped
                continue

        zone_id = random.choice(zone_ids)
        rider_id = random.choice(rider_ids)

        order_value = random.randint(120, 600)
        item_count = random.randint(1, 8)
        weather = random.choices(["Normal", "Rain"], weights=[0.88, 0.12])[0]

        # ------------------ INSERT ORDERS ------------------
        cursor.execute(
            """
            INSERT INTO orders
            (order_id, order_time, zone_id, order_value, item_count, weather)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (order_id, order_time, zone_id, order_value, item_count, weather)
        )

        # ------------------ DELIVERY PIPELINE ------------------
        picking_start = order_time + timedelta(minutes=random.randint(0, 1))
        picking_duration = random.randint(2, 5) + item_count * 0.25
        picking_end = picking_start + timedelta(minutes=picking_duration)

        dispatch_time = picking_end + timedelta(minutes=random.randint(1, 2))

        travel_time = random.uniform(5, 8)

        # zone distance impact
        if zone_id >= 6:
            travel_time += random.uniform(2, 4)

        # peak congestion impact
        if (11 <= order_time.hour < 14) or (17 <= order_time.hour < 21):
            travel_time += random.uniform(4, 7)

        # rain impact
        if weather == "Rain":
            travel_time += random.uniform(2, 4)

        delivery_time = dispatch_time + timedelta(minutes=travel_time)

        # ------------------ INSERT DELIVERY EVENTS ------------------
        cursor.execute(
            """
            INSERT INTO delivery_events
            (order_id, rider_id, picking_start_time, picking_end_time,
             dispatch_time, delivery_time, distance_km)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                order_id,
                rider_id,
                picking_start,
                picking_end,
                dispatch_time,
                delivery_time,
                round(random.uniform(1.2, 6.0), 2)
            )
        )

        order_id += 1

conn.commit()
print("✅ Fresh Coimbatore dataset generated successfully")

