import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

from analytics import (
    load_base_data,
    add_derived_columns,
    overview_module,
    delay_root_cause,
    micro_zone_performance,
    rider_efficiency,
    warehouse_picking,
    zone_optimization_simulation
)

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="Quick Commerce Delivery Intelligence",
    page_icon="🛵",
    layout="wide"
)

# -------------------------------------------------
# ENTERPRISE CSS STYLING
# -------------------------------------------------

st.markdown("""
<style>

body {
    background-color:#f4f7fb;
}

.main-title {
    font-size:42px;
    font-weight:700;
    color:white;
}

.subtitle {
    font-size:18px;
    color:white;
}

.header-container {
    padding:35px;
    border-radius:20px;
    background:linear-gradient(90deg,#ff6a00,#ee0979);
    box-shadow:0 8px 20px rgba(0,0,0,0.25);
}

.kpi-card {
    background:linear-gradient(135deg,#667eea,#764ba2);
    padding:22px;
    border-radius:16px;
    color:white;
    text-align:center;
    box-shadow:0 8px 20px rgba(0,0,0,0.15);
}

.kpi-title {
    font-size:14px;
    opacity:0.85;
}

.kpi-value {
    font-size:28px;
    font-weight:700;
}

.chart-card {
    background:white;
    padding:25px;
    border-radius:18px;
    box-shadow:0px 6px 18px rgba(0,0,0,0.1);
    margin-top:10px;
}

.insight-card {
    background:#eef3ff;
    padding:15px;
    border-radius:12px;
    border-left:5px solid #4f8cff;
    font-size:14px;
}

.sidebar .sidebar-content {
    background:linear-gradient(#141e30,#243b55);
    color:white;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.markdown("""
<div class="header-container">
<div class="main-title">🛵 Quick Commerce Delivery Intelligence</div>
<div class="subtitle">
Enterprise Analytics Dashboard for Last-Mile Delivery Optimization – Coimbatore
</div>
</div>
""", unsafe_allow_html=True)

st.write("")

# -------------------------------------------------
# DATA LOADING
# -------------------------------------------------

@st.cache_data
def load_data():
    df = load_base_data()
    df = add_derived_columns(df)
    return df

df = load_data()

# -------------------------------------------------
# KPI CARD FUNCTION
# -------------------------------------------------

def kpi_card(title,value):

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """,unsafe_allow_html=True)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

st.sidebar.title("📊 Analytics Modules")

module = st.sidebar.radio(
    "Select Analysis",
    [
        "Overview",
        "Delay Root Cause",
        "Micro-Zone Performance",
        "Rider Efficiency",
        "Warehouse Picking",
        "Risk & Simulation"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info("""
Dashboard Modules

Overview → System KPIs  
Delay Root Cause → Delay drivers  
Micro-Zone → Area performance  
Rider Efficiency → Rider productivity  
Warehouse → Picking analysis  
Simulation → SLA optimization
""")

# =================================================
# OVERVIEW
# =================================================

if module == "Overview":

    st.subheader("📌 System Overview")

    kpis = overview_module(df)

    c1,c2,c3,c4,c5 = st.columns(5)

    with c1:
        kpi_card("Total Orders",kpis["Total Orders"])

    with c2:
        kpi_card("Avg Delivery Time",f"{kpis['Avg Delivery Time (min)']} min")

    with c3:
        kpi_card("SLA Compliance",f"{kpis['SLA % (15 min)']}%")

    with c4:
        kpi_card("Peak Orders",f"{kpis['Peak Orders %']}%")

    with c5:
        kpi_card("Night Orders",kpis["Night Orders (1–5 AM)"])

    st.write("")

    sla_df = df.groupby("is_peak")["sla_met"].mean().reset_index()
    sla_df["sla_met"] *= 100

    fig = px.bar(
        sla_df,
        x="is_peak",
        y="sla_met",
        color="is_peak",
        title="SLA Performance: Peak vs Non-Peak Hours"
    )

    st.markdown('<div class="chart-card">',unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True)
    st.markdown('</div>',unsafe_allow_html=True)

    st.markdown("""
    <div class="insight-card">
    Insight: Peak demand periods show reduced SLA compliance indicating rider capacity constraints.
    </div>
    """,unsafe_allow_html=True)

# =================================================
# DELAY ROOT CAUSE
# =================================================

elif module == "Delay Root Cause":

    st.subheader("⏳ Delay Root Cause Analysis")

    heat_df = df.pivot_table(
        values="delivery_minutes",
        index="weather",
        columns="is_peak",
        aggfunc="mean"
    ).round(2)

    fig_heat = px.imshow(
        heat_df,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        title="Delivery Delay Pattern by Weather & Demand"
    )

    st.markdown('<div class="chart-card">',unsafe_allow_html=True)
    st.plotly_chart(fig_heat,use_container_width=True)
    st.markdown('</div>',unsafe_allow_html=True)

    bubble_df = pd.DataFrame({
        "Factor":["Peak Hours","Rain","High Item Count"],
        "Avg Delay":[
            df[df["is_peak"]==1]["delivery_minutes"].mean(),
            df[df["weather"]=="Rain"]["delivery_minutes"].mean(),
            df[df["item_count"]>=5]["delivery_minutes"].mean()
        ],
        "Frequency":[
            len(df[df["is_peak"]==1]),
            len(df[df["weather"]=="Rain"]),
            len(df[df["item_count"]>=5])
        ]
    }).fillna(0)

    fig_bubble = px.scatter(
        bubble_df,
        x="Avg Delay",
        y="Frequency",
        size="Avg Delay",
        color="Factor",
        size_max=60,
        title="Operational Delay Impact Analysis"
    )

    st.markdown('<div class="chart-card">',unsafe_allow_html=True)
    st.plotly_chart(fig_bubble,use_container_width=True)
    st.markdown('</div>',unsafe_allow_html=True)

# =================================================
# MICRO ZONE
# =================================================

elif module == "Micro-Zone Performance":

    st.subheader("📍 Micro-Zone Performance")

    zone_df = micro_zone_performance(df)

    col1,col2 = st.columns(2)

    fig1 = px.bar(zone_df,x="zone_name",y="avg_delivery_time",
                  color="zone_name",title="Average Delivery Time by Zone")

    fig2 = px.bar(zone_df,x="zone_name",y="sla_percent",
                  color="zone_name",title="SLA Compliance by Zone")

    with col1:
        st.markdown('<div class="chart-card">',unsafe_allow_html=True)
        st.plotly_chart(fig1,use_container_width=True)
        st.markdown('</div>',unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">',unsafe_allow_html=True)
        st.plotly_chart(fig2,use_container_width=True)
        st.markdown('</div>',unsafe_allow_html=True)

    st.dataframe(zone_df,use_container_width=True)

# =================================================
# RIDER
# =================================================

elif module == "Rider Efficiency":

    st.subheader("🧑‍✈️ Rider Efficiency")

    rider_df = rider_efficiency(df)

    fig = px.scatter(
        rider_df,
        x="avg_delivery_time",
        y="sla_percent",
        size="orders_handled",
        color="rider_name",
        hover_name="rider_name",
        title="Rider Performance Analysis"
    )

    st.markdown('<div class="chart-card">',unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True)
    st.markdown('</div>',unsafe_allow_html=True)

    st.dataframe(rider_df,use_container_width=True)

# =================================================
# WAREHOUSE
# =================================================

elif module == "Warehouse Picking":

    st.subheader("🏬 Warehouse Picking Efficiency")

    picking = warehouse_picking(df)

    c1,c2,c3 = st.columns(3)

    with c1:
        kpi_card("Avg Picking Time",f"{picking['Avg Picking Time (min)']} min")

    with c2:
        kpi_card("Max Picking Time",f"{picking['Max Picking Time (min)']} min")

    with c3:
        kpi_card("Picking Contribution",f"{picking['Picking Contribution %']}%")

    fig = px.box(df,y="picking_minutes",points="all",
                 title="Warehouse Picking Time Distribution")

    st.markdown('<div class="chart-card">',unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True)
    st.markdown('</div>',unsafe_allow_html=True)

# =================================================
# SIMULATION
# =================================================

elif module == "Risk & Simulation":

    st.subheader("⚙️ Operational Optimization Simulation")

    zone_list = sorted(df["zone_name"].unique())

    selected_zone = st.selectbox("Select Zone",zone_list)

    extra_riders = st.slider("Additional Riders",0,5,2)
    order_reduction = st.slider("Order Reduction (%)",0,40,15,5)

    result = zone_optimization_simulation(
        df,
        selected_zone,
        extra_riders,
        order_reduction
    )

    if result:

        c1,c2,c3 = st.columns(3)

        with c1:
            kpi_card("Base SLA",f"{result['Base SLA %']}%")

        with c2:
            kpi_card("Optimized SLA",f"{result['Optimized SLA %']}%")

        with c3:
            kpi_card("Improvement",f"{result['SLA Improvement %']}%")

        compare_df = pd.DataFrame({
            "Scenario":["Before","After"],
            "SLA":[result["Base SLA %"],result["Optimized SLA %"]]
        })

        fig = px.bar(
            compare_df,
            x="Scenario",
            y="SLA",
            color="Scenario",
            title="SLA Optimization Result"
        )

        st.markdown('<div class="chart-card">',unsafe_allow_html=True)
        st.plotly_chart(fig,use_container_width=True)
        st.markdown('</div>',unsafe_allow_html=True)