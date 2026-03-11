import pandas as pd
import numpy as np


# ==================================================
# LOAD BASE DATA FROM CSV
# ==================================================

def load_base_data():

    df = pd.read_csv("delivery_dataset.csv")

    # convert order time
    if "order_time" in df.columns:
        df["order_time"] = pd.to_datetime(df["order_time"])

    return df


# ==================================================
# DERIVED METRICS
# ==================================================

def add_derived_columns(df):

    df = df.copy()

    # hour extraction
    df["hour"] = df["order_time"].dt.hour

    # SLA flag
    df["sla_met"] = df["delivery_minutes"] <= 15

    # peak hours
    df["is_peak"] = df["hour"].apply(
        lambda x: "Peak" if (11 <= x < 14 or 17 <= x < 21) else "Non-Peak"
    )

    # night flag
    df["is_night"] = df["hour"].apply(
        lambda x: True if 1 <= x < 5 else False
    )

    return df


# ==================================================
# 1️⃣ OVERVIEW MODULE
# ==================================================

def overview_module(df):

    return {
        "Total Orders": len(df),
        "Avg Delivery Time (min)": round(df["delivery_minutes"].mean(), 2),
        "SLA % (15 min)": round(df["sla_met"].mean() * 100, 2),
        "Peak Orders %": round((df["is_peak"] == "Peak").mean() * 100, 2),
        "Night Orders (1–5 AM)": int(df["is_night"].sum())
    }


# ==================================================
# 2️⃣ DELAY ROOT CAUSE
# ==================================================

def delay_root_cause(df):

    causes = {

        "Peak Hours":
            df[df["is_peak"] == "Peak"]["delivery_minutes"].mean(),

        "Non-Peak Hours":
            df[df["is_peak"] == "Non-Peak"]["delivery_minutes"].mean(),

        "Rain":
            df[df["weather"] == "Rain"]["delivery_minutes"].mean(),

        "Normal Weather":
            df[df["weather"] == "Normal"]["delivery_minutes"].mean(),

        "High Item Count (≥5)":
            df[df["item_count"] >= 5]["delivery_minutes"].mean(),

        "Low Item Count (<5)":
            df[df["item_count"] < 5]["delivery_minutes"].mean()
    }

    return {k: round(v, 2) for k, v in causes.items()}


# ==================================================
# 3️⃣ MICRO-ZONE PERFORMANCE
# ==================================================

def micro_zone_performance(df):

    zone_perf = (
        df.groupby("zone_name")
        .agg(
            total_orders=("order_id", "count"),
            avg_delivery_time=("delivery_minutes", "mean"),
            sla_percent=("sla_met", "mean")
        )
        .reset_index()
    )

    zone_perf["avg_delivery_time"] = round(
        zone_perf["avg_delivery_time"], 2
    )

    zone_perf["sla_percent"] = round(
        zone_perf["sla_percent"] * 100, 2
    )

    return zone_perf


# ==================================================
# 4️⃣ RIDER EFFICIENCY
# ==================================================

def rider_efficiency(df):

    rider_perf = (
        df.groupby("rider_name")
        .agg(
            orders_handled=("order_id", "count"),
            avg_delivery_time=("delivery_minutes", "mean"),
            sla_percent=("sla_met", "mean"),
            avg_distance_km=("distance_km", "mean")
        )
        .reset_index()
    )

    rider_perf["avg_delivery_time"] = round(
        rider_perf["avg_delivery_time"], 2
    )

    rider_perf["sla_percent"] = round(
        rider_perf["sla_percent"] * 100, 2
    )

    rider_perf["avg_distance_km"] = round(
        rider_perf["avg_distance_km"], 2
    )

    return rider_perf


# ==================================================
# 5️⃣ WAREHOUSE PICKING
# ==================================================

def warehouse_picking(df):

    return {

        "Avg Picking Time (min)":
            round(df["picking_minutes"].mean(), 2),

        "Max Picking Time (min)":
            round(df["picking_minutes"].max(), 2),

        "Picking Contribution %":
            round(
                (df["picking_minutes"].mean()
                 / df["delivery_minutes"].mean()) * 100,
                2
            )
    }


# ==================================================
# 6️⃣ ZONE OPTIMIZATION SIMULATION
# ==================================================

def zone_optimization_simulation(
    df,
    zone_name,
    extra_riders=0,
    order_reduction_pct=0
):

    zone_df = df[df["zone_name"] == zone_name].copy()

    if zone_df.empty:
        return None

    base_sla = zone_df["sla_met"].mean() * 100

    rider_effect = 1 - (extra_riders * 0.07)
    rider_effect = max(rider_effect, 0.7)

    order_effect = 1 - (order_reduction_pct / 100 * 0.4)

    zone_df["optimized_delivery"] = (
        zone_df["delivery_minutes"]
        * rider_effect
        * order_effect
    )

    optimized_sla = (
        zone_df["optimized_delivery"] <= 15
    ).mean() * 100

    return {

        "Zone": zone_name,
        "Base SLA %": round(base_sla, 2),
        "Optimized SLA %": round(optimized_sla, 2),
        "SLA Improvement %": round(
            optimized_sla - base_sla, 2
        ),
        "Extra Riders Added": extra_riders,
        "Order Reduction %": order_reduction_pct
    }
