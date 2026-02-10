import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Page config ----------------
st.set_page_config(layout="wide")
st.title("Tableau de Bord Marketing NovaRetail")
st.markdown("---")

# ---------------- Load data ----------------
df_final = pd.read_parquet("df_final.parquet")
df_campaign = pd.read_parquet("df_campaign.parquet")

# ---------------- Color palette (same vibe, different shades) ----------------
CHANNEL_ORDER = ["Emailing", "Google Ads", "LinkedIn Ads"]
CHANNEL_COLORS = {
    "Emailing": "#86C5FF",     # light blue
    "Google Ads": " #ea4335",   # medium red
    "LinkedIn Ads": "#0072b1"  # deeper blue
}

# ---------------- Ensure KPI columns exist ----------------
required_kpis = {"CTR", "Taux_de_conversion", "CPL"}
if not df_campaign.empty:
    if "CTR" not in df_campaign.columns:
        df_campaign["CTR"] = df_campaign["clicks"] / df_campaign["impressions"]
    if "Taux_de_conversion" not in df_campaign.columns:
        df_campaign["Taux_de_conversion"] = df_campaign["conversions"] / df_campaign["clicks"]
    if "CPL" not in df_campaign.columns:
        df_campaign["CPL"] = df_campaign["cost"] / df_campaign["conversions"]

if df_final is None or df_final.empty:
    st.warning("df_final est vide ou non défini. Vérifie ton bloc amont (merge + filtre octobre 2025).")
    st.stop()

missing_cols = required_kpis - set(df_final.columns)
if missing_cols:
    st.error(
        f"df_final ne contient pas les colonnes KPI attendues : {missing_cols}. "
        "Assure-toi d'avoir mergé les KPI campagne dans df_final."
    )
    st.stop()

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filtres")

selected_channel = st.sidebar.multiselect(
    "Sélectionnez le Canal Marketing:",
    options=[c for c in CHANNEL_ORDER if c in df_final["channel"].dropna().unique()],
    default=[c for c in CHANNEL_ORDER if c in df_final["channel"].dropna().unique()],
)

selected_company_size = st.sidebar.multiselect(
    "Sélectionnez la Taille d'Entreprise:",
    options=sorted(df_final["company_size"].dropna().unique()),
    default=sorted(df_final["company_size"].dropna().unique()),
)

selected_sector = st.sidebar.multiselect(
    "Sélectionnez le Secteur:",
    options=sorted(df_final["sector"].dropna().unique()),
    default=sorted(df_final["sector"].dropna().unique()),
)

selected_region = st.sidebar.multiselect(
    "Sélectionnez la Région:",
    options=sorted(df_final["region"].dropna().unique()),
    default=sorted(df_final["region"].dropna().unique()),
)

# ---------------- Filtered dataset ----------------
df_selection = df_final[
    df_final["channel"].isin(selected_channel)
    & df_final["company_size"].isin(selected_company_size)
    & df_final["sector"].isin(selected_sector)
    & df_final["region"].isin(selected_region)
].copy()

if df_selection.empty:
    st.warning("Aucune donnée pour ces filtres. Essaie d'élargir la sélection.")
    st.stop()

# ---------------- KPIs ----------------
st.subheader("KPIs Clés")
k1, k2, k3, k4, k5 = st.columns(5)

total_leads = df_selection.shape[0]
total_clients = (df_selection["status"] == "Client").sum()

avg_ctr = df_selection["CTR"].mean()
avg_conv_rate = df_selection["Taux_de_conversion"].mean()
avg_cpl = df_selection["CPL"].mean()

with k1:
    st.metric("Total Leads", f"{total_leads}")
with k2:
    st.metric("Clients", f"{total_clients}")
with k3:
    st.metric("Taux de Conversion Moyen", f"{avg_conv_rate:.2%}")
with k4:
    st.metric("CTR Moyen", f"{avg_ctr:.2%}")
with k5:
    st.metric("CPL Moyen", f"{avg_cpl:.2f} €")

st.markdown("---")

# ---------------- Charts: Channel KPIs ----------------
st.subheader("Analyse par Canal Marketing")
c1, c2 = st.columns(2)

with c1:
    ctr_by_channel = df_selection.groupby("channel", as_index=False)["CTR"].mean()
    fig_ctr = px.bar(
        ctr_by_channel,
        x="channel", y="CTR",
        color="channel",
        color_discrete_map=CHANNEL_COLORS,
        category_orders={"channel": CHANNEL_ORDER},
        title="CTR moyen par canal",
        labels={"channel": "Canal marketing", "CTR": "CTR moyen"},
    )
    fig_ctr.update_yaxes(tickformat=".2%")
    fig_ctr.update_layout(showlegend=False)
    st.plotly_chart(fig_ctr, use_container_width=True)

with c2:
    conv_by_channel = df_selection.groupby("channel", as_index=False)["Taux_de_conversion"].mean()
    fig_conv = px.bar(
        conv_by_channel,
        x="channel", y="Taux_de_conversion",
        color="channel",
        color_discrete_map=CHANNEL_COLORS,
        category_orders={"channel": CHANNEL_ORDER},
        title="Taux de conversion moyen par canal",
        labels={"channel": "Canal marketing", "Taux_de_conversion": "Taux de conversion moyen"},
    )
    fig_conv.update_yaxes(tickformat=".2%")
    fig_conv.update_layout(showlegend=False)
    st.plotly_chart(fig_conv, use_container_width=True)

st.markdown("---")

# ---------------- CPL + status distribution ----------------
st.subheader("Coût par Lead (CPL) et Distribution des Leads")
c3, c4 = st.columns(2)

with c3:
    cpl_by_channel = df_selection.groupby("channel", as_index=False)["CPL"].mean()
    fig_cpl = px.bar(
        cpl_by_channel,
        x="channel", y="CPL",
        color="channel",
        color_discrete_map=CHANNEL_COLORS,
        category_orders={"channel": CHANNEL_ORDER},
        title="CPL moyen par canal",
        labels={"channel": "Canal marketing", "CPL": "CPL moyen (€)"},
    )
    fig_cpl.update_layout(showlegend=False)
    st.plotly_chart(fig_cpl, use_container_width=True)

with c4:
    status_distribution = df_selection["status"].value_counts().reset_index()
    status_distribution.columns = ["Statut", "Nombre de leads"]
    fig_status = px.pie(
        status_distribution,
        values="Nombre de leads",
        names="Statut",
        title="Distribution des leads par statut",
    )
    st.plotly_chart(fig_status, use_container_width=True)

st.markdown("---")

# ---------------- Detailed analysis ----------------
st.subheader("Analyse Détaillée des Leads")
c5, c6 = st.columns(2)

with c5:
    company_size_status = df_selection.groupby(["company_size", "status"]).size().reset_index(name="count")
    fig_company = px.bar(
        company_size_status,
        x="company_size", y="count", color="status",
        title="Leads par taille d'entreprise et statut",
        labels={"company_size": "Taille d'entreprise", "count": "Nombre de leads", "status": "Statut"},
        category_orders={"company_size": ["1-10", "10-50", "50-100", "100-500"]},
    )
    st.plotly_chart(fig_company, use_container_width=True)

with c6:
    sector_status = df_selection.groupby(["sector", "status"]).size().reset_index(name="count")
    fig_sector = px.bar(
        sector_status,
        x="sector", y="count", color="status",
        title="Leads par secteur et statut",
        labels={"sector": "Secteur", "count": "Nombre de leads", "status": "Statut"},
    )
    st.plotly_chart(fig_sector, use_container_width=True)

st.markdown("---")

# ---------------- Geography heatmap ----------------
st.subheader("Analyse Géographique")
region_status_crosstab = pd.crosstab(df_selection["region"], df_selection["status"], normalize="index")

fig_heatmap = px.imshow(
    region_status_crosstab,
    text_auto=True,
    aspect="auto",
    labels=dict(x="Statut du lead", y="Région", color="Proportion"),
    x=region_status_crosstab.columns,
    y=region_status_crosstab.index,
    title="Proportion des statuts de leads par région",
)
fig_heatmap.update_coloraxes(colorbar_tickformat=".0%")
st.plotly_chart(fig_heatmap, use_container_width=True)

# ---------------- Optional: show data ----------------
with st.expander("Afficher les données filtrées"):
    st.dataframe(df_selection)

