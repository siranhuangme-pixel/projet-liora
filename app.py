"""
Dashboard interactif — Prédiction du taux d'incidence (allergie/asthme/bronchiolite)
Projet DataScientest / Liora — Direction de l'Actuariat Vie

Lancement : streamlit run app.py
"""

import json
import urllib.request
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(
    page_title="Urgences allergie/asthme/bronchiolite — Dashboard",
    page_icon="🏥",
    layout="wide",
)

TABLES_DIR = Path("data/processed")

MOIS_LABELS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
               "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]

Y_INDICATEURS = {
    "Urgences": "taux_urgences",
    "Hospitalisations post-urgences": "taux_hosp",
    "Actes SOS Médecins": "taux_sos",
}
PATHOLOGIES = ["Allergie", "Asthme", "Bronchiolite"]
COLORS = {"Allergie": "#E74C3C", "Asthme": "#2980B9", "Bronchiolite": "#27AE60"}

FEATURES_CORR = [
    "temp_moy", "temp_min", "temp_max", "humidite_moy", "vent_moy", "precip_total",
    "pm10_moy", "pm25_moy", "no2_moy", "o3_moy", "so2_moy",
    "pollen_graminees_moy", "pollen_betula_moy", "pollen_alnus_moy",
    "pollen_ambrosia_moy", "pollen_artemisia_moy", "pollen_platane_moy",
    "pollen_urticacees_moy", "moisissure_alternaria_moy", "moisissure_cladosporium_moy",
    "part_seniors", "part_jeunes", "tx_urbain", "densite_med_gen",
    "prev_resp_chronique", "tx_cadres", "tx_ouvriers",
]

# Mêmes métadonnées que le dictionnaire de données de 03_eda.ipynb
DICO_VARIABLES = {
    "dept": ("Clé", "Code département INSEE (01-95, 2A, 2B)", "—"),
    "annee_mois": ("Clé", "Période mensuelle (YYYY-MM)", "—"),
    "taux_urgences_allergie": ("Cible (Y)", "Part des passages aux urgences pour allergie (/100k urgences toutes causes)", "Santé Publique France (Odissé)"),
    "taux_hosp_allergie": ("Cible (Y)", "Part des hospitalisations post-urgences pour allergie (/100k toutes causes)", "Santé Publique France (Odissé)"),
    "taux_sos_allergie": ("Cible (Y)", "Part des actes SOS Médecins pour allergie (/100k toutes causes)", "Santé Publique France (Odissé)"),
    "taux_urgences_asthme": ("Cible (Y)", "Part des passages aux urgences pour asthme (/100k toutes causes)", "Santé Publique France (Odissé)"),
    "taux_hosp_asthme": ("Cible (Y)", "Part des hospitalisations post-urgences pour asthme (/100k toutes causes)", "Santé Publique France (Odissé)"),
    "taux_sos_asthme": ("Cible (Y)", "Part des actes SOS Médecins pour asthme (/100k toutes causes)", "Santé Publique France (Odissé)"),
    "taux_urgences_bronchiolite": ("Cible (Y)", "Part des passages aux urgences pour bronchiolite, 0 an (/100k toutes causes)", "Santé Publique France (Odissé)"),
    "taux_hosp_bronchiolite": ("Cible (Y)", "Part des hospitalisations post-urgences pour bronchiolite, 0 an (/100k toutes causes)", "Santé Publique France (Odissé)"),
    "taux_sos_bronchiolite": ("Cible (Y)", "Part des actes SOS Médecins pour bronchiolite, 0 an (/100k toutes causes)", "Santé Publique France (Odissé)"),
    "annee": ("Temporelle", "Année calendaire", "Calculé"),
    "mois": ("Temporelle", "Mois calendaire (1-12)", "Calculé"),
    "trimestre": ("Temporelle", "Trimestre (1-4)", "Calculé"),
    "semestre": ("Temporelle", "Semestre (1-2)", "Calculé"),
    "sin_mois": ("Temporelle", "Encodage cyclique du mois (sinus)", "Calculé"),
    "cos_mois": ("Temporelle", "Encodage cyclique du mois (cosinus)", "Calculé"),
    "est_hiver": ("Temporelle", "1 si mois d'hiver", "Calculé"),
    "est_printemps": ("Temporelle", "1 si mois de printemps", "Calculé"),
    "est_ete": ("Temporelle", "1 si mois d'été", "Calculé"),
    "est_automne": ("Temporelle", "1 si mois d'automne", "Calculé"),
    "saison_pollen": ("Temporelle", "1 si mois de forte pollinisation", "Calculé"),
    "flag_covid": ("Temporelle", "1 pendant la période Covid (~03/2020-04/2022)", "Calculé"),
    "temp_moy": ("Météo", "Température moyenne mensuelle (°C)", "Météo France (MENSQ)"),
    "temp_max": ("Météo", "Moyenne mensuelle des températures maximales (°C)", "Météo France (MENSQ)"),
    "temp_min": ("Météo", "Moyenne mensuelle des températures minimales (°C)", "Météo France (MENSQ)"),
    "humidite_moy": ("Météo", "Humidité relative moyenne (%)", "Météo France (MENSQ)"),
    "vent_moy": ("Météo", "Vitesse moyenne du vent à 10m (m/s)", "Météo France (MENSQ)"),
    "precip_total": ("Météo", "Cumul mensuel des précipitations (mm)", "Météo France (MENSQ)"),
    "pop_totale": ("Démographie", "Population totale du département (2024)", "CNAM (Cartographie des pathologies)"),
    "part_seniors": ("Démographie", "Part de la population ≥ 65 ans", "CNAM (Cartographie des pathologies)"),
    "part_jeunes": ("Démographie", "Part de la population < 15 ans", "CNAM (Cartographie des pathologies)"),
    "prev_resp_chronique": ("Démographie", "Prévalence maladies respiratoires chroniques (proxy vulnérabilité)", "CNAM (Cartographie des pathologies)"),
    "tx_urbain": ("Démographie", "Part de la population en unité urbaine (2017)", "INSEE (Unités urbaines)"),
    "densite_med_gen": ("Démographie", "Densité médecins généralistes /100k hab", "Ameli"),
    "densite_spe": ("Démographie", "Densité médecins spécialistes /100k hab", "Ameli"),
    "densite_medecins": ("Démographie", "Densité de médecins (tous exercices) /100k hab — varie par année", "DREES (RPPS)"),
    "tx_agriculteurs": ("Socio-pro", "Part des agriculteurs exploitants (2022)", "INSEE"),
    "tx_artisans": ("Socio-pro", "Part des artisans, commerçants, chefs d'entreprise", "INSEE"),
    "tx_cadres": ("Socio-pro", "Part des cadres, professions intellectuelles supérieures", "INSEE"),
    "tx_prof_interm": ("Socio-pro", "Part des professions intermédiaires", "INSEE"),
    "tx_employes": ("Socio-pro", "Part des employés", "INSEE"),
    "tx_ouvriers": ("Socio-pro", "Part des ouvriers", "INSEE"),
    "tx_autres": ("Socio-pro", "Autres (sans activité identifiée)", "INSEE"),
    "Hopitaux": ("Établissements de santé", "Nombre d'hôpitaux par département et par année", "FINESS"),
    "Pharmacies": ("Établissements de santé", "Nombre de pharmacies par département et par année", "FINESS"),
    "Laboratoires": ("Établissements de santé", "Nombre de laboratoires d'analyses médicales par département et par année", "FINESS"),
    "cont_ind_vieillisement_pop": ("Contexte socio-éco", "Indice de vieillissement de la population (65+ / -20 ans)", "DREES (ISD)"),
    "cont_part_pop_pole_urbain": ("Contexte socio-éco", "Part de la population vivant dans un pôle urbain — pas publié tous les ans", "DREES (ISD)"),
    "cont_tx_act": ("Contexte socio-éco", "Taux d'activité — pas publié tous les ans", "DREES (ISD)"),
    "cont_part_csp_cadres": ("Contexte socio-éco", "Part des cadres et professions intellectuelles supérieures — pas publié tous les ans", "DREES (ISD)"),
    "pop_m25": ("Contexte socio-éco", "Population de moins de 25 ans", "DREES (ISD)"),
    "pop_25_64": ("Contexte socio-éco", "Population 25-64 ans", "DREES (ISD)"),
    "pop_65p": ("Contexte socio-éco", "Population 65 ans et plus", "DREES (ISD)"),
    "chom_pop_age_trav": ("Contexte socio-éco", "Taux de chômage rapporté à la population en âge de travailler", "DREES (ISD)"),
    "no_moy": ("Qualité de l'air", "Concentration mensuelle moyenne NO (µg/m³)", "LCSQA / AASQA"),
    "no2_moy": ("Qualité de l'air", "Concentration mensuelle moyenne NO2 (µg/m³)", "LCSQA / AASQA"),
    "o3_moy": ("Qualité de l'air", "Concentration mensuelle moyenne O3 (µg/m³)", "LCSQA / AASQA"),
    "pm10_moy": ("Qualité de l'air", "Concentration mensuelle moyenne PM10 (µg/m³)", "LCSQA / AASQA"),
    "pm25_moy": ("Qualité de l'air", "Concentration mensuelle moyenne PM2.5 (µg/m³)", "LCSQA / AASQA"),
    "so2_moy": ("Qualité de l'air", "Concentration mensuelle moyenne SO2 (µg/m³) — peu de stations", "LCSQA / AASQA"),
    "nb_jours_pm10_eleve_est": ("Qualité de l'air", "Estimation nb jours/mois PM10 > 50µg/m³ (seuil OMS)", "LCSQA / AASQA"),
    "pollen_betula_moy": ("Pollen/moisissures", "Concentration moyenne pollen bouleau (grains/m³)", "RNSA"),
    "pollen_graminees_moy": ("Pollen/moisissures", "Concentration moyenne pollen graminées (grains/m³)", "RNSA"),
    "pollen_artemisia_moy": ("Pollen/moisissures", "Concentration moyenne pollen armoise (grains/m³)", "RNSA"),
    "pollen_ambrosia_moy": ("Pollen/moisissures", "Concentration moyenne pollen ambroisie (grains/m³)", "RNSA"),
    "pollen_alnus_moy": ("Pollen/moisissures", "Concentration moyenne pollen aulne (grains/m³)", "RNSA"),
    "pollen_urticacees_moy": ("Pollen/moisissures", "Concentration moyenne pollen urticacées (grains/m³)", "RNSA"),
    "pollen_platane_moy": ("Pollen/moisissures", "Concentration moyenne pollen platane (grains/m³)", "RNSA"),
    "moisissure_cladosporium_moy": ("Pollen/moisissures", "Concentration moyenne spores Cladosporium (grains/m³)", "RNSA"),
    "moisissure_alternaria_moy": ("Pollen/moisissures", "Concentration moyenne spores Alternaria (grains/m³)", "RNSA"),
    "pollen_global_max": ("Pollen/moisissures", "Concentration max tous pollens confondus (grains/m³)", "RNSA"),
    "nb_jours_eleve": ("Pollen/moisissures", "⚠️ 0/1 = 'au moins un jour élevé ce mois', pas un nombre de jours (bug connu)", "RNSA"),
    "nb_incendies": ("Incendies", "Nombre d'incendies de forêt recensés dans le mois", "BDIFF"),
    "surface_parcourue_ha": ("Incendies", "Surface totale parcourue par le feu dans le mois (hectares)", "BDIFF"),
}


@st.cache_data
def load_data():
    df = pd.read_parquet(TABLES_DIR / "df_model.parquet")
    df["annee_mois_dt"] = pd.to_datetime(df["annee_mois"] + "-01")
    df["mois"] = df["annee_mois_dt"].dt.month
    df["annee"] = df["annee_mois_dt"].dt.year
    return df


@st.cache_data
def lister_tables():
    fichiers = ["fact_urgences.parquet"] + sorted(p.name for p in TABLES_DIR.glob("dim_*.parquet"))
    return [f for f in fichiers if (TABLES_DIR / f).exists()]


@st.cache_data
def load_table(nom_fichier):
    return pd.read_parquet(TABLES_DIR / nom_fichier)


@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.load(r)
    except Exception:
        return None


df_full = load_data()

# ── Sidebar : filtres globaux ─────────────────────────────────────────────
st.sidebar.title("🏥 Filtres")

patho_label = st.sidebar.radio("Pathologie", PATHOLOGIES, index=0)
indic_label = st.sidebar.radio("Indicateur", list(Y_INDICATEURS.keys()), index=0)
col_y = f"{Y_INDICATEURS[indic_label]}_{patho_label.lower()}"

depts_dispo = sorted(df_full["dept"].unique())
depts_choisis = st.sidebar.multiselect(
    "Départements (vide = tous)", depts_dispo, default=[]
)

annees_dispo = sorted(df_full["annee"].unique())
annee_min, annee_max = st.sidebar.select_slider(
    "Période",
    options=annees_dispo,
    value=(annees_dispo[0], annees_dispo[-1]),
)

df = df_full[(df_full["annee"] >= annee_min) & (df_full["annee"] <= annee_max)].copy()
if depts_choisis:
    df = df[df["dept"].isin(depts_choisis)]

st.sidebar.markdown("---")
st.sidebar.caption(
    f"{df['dept'].nunique()} départements · {df.shape[0]:,} lignes filtrées\n\n"
    f"⚠️ Les `taux_*` sont des **parts relatives** parmi les urgences/hospitalisations/"
    f"actes SOS toutes causes du même sous-groupe — pas des taux d'incidence en population."
)

st.title("🏥 Urgences allergie · asthme · bronchiolite")
st.caption("Projet DataScientest / Liora — Direction de l'Actuariat Vie")

tab_tables, tab_evol, tab_carte, tab_corr, tab_facteurs, tab_qualite, tab_dico = st.tabs([
    "🔍 Tables brutes",
    "📈 Évolution & saisonnalité",
    "🗺️ Carte & classement",
    "🔗 Corrélations",
    "🌦️ Facteurs environnementaux",
    "📉 Qualité des données",
    "📖 Dictionnaire des données",
])

# ═══════════════════════════════════════════════════════════════════════
# TAB 0 — Tables brutes (sanity check table par table, avant df_model)
# ═══════════════════════════════════════════════════════════════════════
with tab_tables:
    st.caption(
        "Chaque dim_*.parquet + fact_urgences pris séparément, avant fusion — "
        "pour repérer une valeur aberrante avant qu'elle ne se retrouve dans df_model."
    )
    nom_fichier = st.selectbox("Table", lister_tables())
    df_t = load_table(nom_fichier)

    st.caption(f"{df_t.shape[0]:,} lignes · {df_t.shape[1]} colonnes")

    missing = (df_t.isnull().mean() * 100).sort_values(ascending=False)
    missing = missing[missing > 0]
    if not missing.empty:
        st.write("Manquants : " + ", ".join(f"`{c}` {p:.0f}%" for c, p in missing.items()))

    cols_num = df_t.select_dtypes(include="number").columns.tolist()

    if cols_num:
        ncols = 4
        nrows = -(-len(cols_num) // ncols)
        fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=cols_num)
        for i, col in enumerate(cols_num):
            r, c = divmod(i, ncols)
            fig.add_trace(go.Histogram(x=df_t[col].dropna(), showlegend=False), row=r + 1, col=c + 1)
        fig.update_layout(title="Distributions", height=260 * nrows, template="plotly_white")
        st.plotly_chart(fig, width="stretch")

    if "annee_mois" in df_t.columns and cols_num:
        df_moy = df_t.groupby("annee_mois")[cols_num].mean().reset_index()
        ncols2 = 3
        nrows2 = -(-len(cols_num) // ncols2)
        fig2 = make_subplots(rows=nrows2, cols=ncols2, subplot_titles=cols_num)
        for i, col in enumerate(cols_num):
            r, c = divmod(i, ncols2)
            fig2.add_trace(go.Scatter(x=df_moy["annee_mois"], y=df_moy[col], mode="lines", showlegend=False), row=r + 1, col=c + 1)
        fig2.update_layout(
            title="Évolution mensuelle (moyenne nationale)",
            height=230 * nrows2, template="plotly_white",
        )
        fig2.update_xaxes(tickangle=45)
        st.plotly_chart(fig2, width="stretch")

# ═══════════════════════════════════════════════════════════════════════
# TAB 1 — Évolution & saisonnalité
# ═══════════════════════════════════════════════════════════════════════
with tab_evol:
    if col_y not in df.columns:
        st.warning(f"Colonne {col_y} introuvable.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            df_nat = df.groupby("annee_mois_dt")[col_y].mean().reset_index()
            fig = go.Figure(go.Scatter(
                x=df_nat["annee_mois_dt"], y=df_nat[col_y],
                mode="lines", fill="tozeroy",
                line=dict(color=COLORS[patho_label], width=2),
                hovertemplate="%{x|%b %Y}<br>Part : %{y:.1f} /100k<extra></extra>",
            ))
            fig.add_vrect(x0="2020-03-01", x1="2022-04-01",
                          fillcolor="gray", opacity=0.08,
                          annotation_text="Covid", annotation_position="top left")
            fig.update_layout(
                title=f"Évolution — {indic_label} {patho_label}",
                yaxis_title="Part (/100k, toutes causes)",
                template="plotly_white", height=420,
            )
            st.plotly_chart(fig, width="stretch")

        with c2:
            df_sais = df.groupby("mois")[col_y].mean().reindex(range(1, 13)).reset_index()
            df_sais["mois_label"] = df_sais["mois"].apply(lambda m: MOIS_LABELS[m - 1])
            idx_max = df_sais[col_y].idxmax()
            bar_colors = [COLORS[patho_label] if i == idx_max else "#BDC3C7"
                          for i in range(12)]
            fig = go.Figure(go.Bar(
                x=df_sais["mois_label"], y=df_sais[col_y],
                marker_color=bar_colors,
                hovertemplate="%{x}<br>Part moyenne : %{y:.1f}<extra></extra>",
            ))
            fig.update_layout(
                title=f"Saisonnalité — {indic_label} {patho_label}",
                yaxis_title="Part moyenne (/100k)",
                template="plotly_white", height=420,
            )
            st.plotly_chart(fig, width="stretch")

        st.subheader("Top 5 départements")
        top5 = df.groupby("dept")[col_y].mean().nlargest(5).index.tolist()
        df_top = df[df["dept"].isin(top5)]
        df_top_mois = df_top.groupby(["annee_mois_dt", "dept"])[col_y].mean().reset_index()
        fig = px.line(
            df_top_mois, x="annee_mois_dt", y=col_y, color="dept",
            labels={col_y: "Part (/100k)", "annee_mois_dt": "Date", "dept": "Dept"},
            template="plotly_white", height=400,
        )
        fig.add_vrect(x0="2020-03-01", x1="2022-04-01", fillcolor="gray", opacity=0.07)
        st.plotly_chart(fig, width="stretch")

# ═══════════════════════════════════════════════════════════════════════
# TAB 2 — Carte & classement
# ═══════════════════════════════════════════════════════════════════════
with tab_carte:
    if col_y not in df.columns:
        st.warning(f"Colonne {col_y} introuvable.")
    else:
        df_dept_moy = df.groupby("dept")[col_y].mean().reset_index()

        geojson_depts = load_geojson()
        if geojson_depts:
            fig = px.choropleth(
                df_dept_moy, geojson=geojson_depts, locations="dept",
                featureidkey="properties.code", color=col_y,
                color_continuous_scale="Reds",
                labels={col_y: "Part (/100k)"},
                hover_data={"dept": True, col_y: ":.1f"},
            )
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                title=f"Carte — {indic_label} {patho_label}",
                margin={"r": 0, "t": 40, "l": 0, "b": 0},
                height=550, template="plotly_white",
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("GeoJSON indisponible (pas de connexion internet) — carte masquée.")

        df_sorted = df_dept_moy.sort_values(col_y, ascending=True)
        fig = go.Figure(go.Bar(
            x=df_sorted[col_y], y=df_sorted["dept"], orientation="h",
            marker=dict(color=df_sorted[col_y], colorscale="Reds",
                       showscale=True, colorbar=dict(title="Part /100k")),
            hovertemplate="Dept %{y}<br>Part : %{x:.1f} /100k<extra></extra>",
        ))
        fig.update_layout(
            title=f"Classement des départements — {indic_label} {patho_label}",
            xaxis_title="Part moyenne (/100k)", yaxis_title="Département",
            height=max(500, len(df_sorted) * 15), template="plotly_white",
        )
        st.plotly_chart(fig, width="stretch")

# ═══════════════════════════════════════════════════════════════════════
# TAB 3 — Corrélations
# ═══════════════════════════════════════════════════════════════════════
with tab_corr:
    cols_y_all = [f"{prefix}_{p.lower()}" for prefix in Y_INDICATEURS.values() for p in PATHOLOGIES]
    cols_dispo = [c for c in cols_y_all + FEATURES_CORR if c in df.columns]
    corr_matrix = df[cols_dispo].corr(method="pearson").round(3)

    fig = go.Figure(go.Heatmap(
        z=corr_matrix.values, x=corr_matrix.columns.tolist(), y=corr_matrix.index.tolist(),
        colorscale="RdBu_r", zmid=0, zmin=-1, zmax=1,
        text=corr_matrix.values.round(2), texttemplate="%{text}", textfont={"size": 7},
        hovertemplate="%{y} × %{x}<br>r = %{z:.3f}<extra></extra>",
    ))
    fig.update_layout(
        title="Matrice de corrélation de Pearson", height=800, template="plotly_white",
        xaxis=dict(tickangle=45),
    )
    st.plotly_chart(fig, width="stretch")

    if col_y in corr_matrix.columns:
        top_corr = (
            corr_matrix[col_y]
            .drop(cols_y_all, errors="ignore")
            .sort_values(key=abs, ascending=True)
            .tail(15)
        )
        bar_colors = ["#E74C3C" if v > 0 else "#2980B9" for v in top_corr.values]
        fig = go.Figure(go.Bar(
            y=top_corr.index.tolist(), x=top_corr.values, orientation="h",
            marker_color=bar_colors,
            hovertemplate="%{y}<br>r = %{x:.3f}<extra></extra>",
        ))
        fig.update_layout(
            title=f"Top 15 corrélations — {indic_label} {patho_label} (rouge=positif, bleu=négatif)",
            xaxis_title="Corrélation de Pearson", xaxis_range=[-1, 1],
            height=550, template="plotly_white",
        )
        st.plotly_chart(fig, width="stretch")

# ═══════════════════════════════════════════════════════════════════════
# TAB 4 — Facteurs environnementaux
# ═══════════════════════════════════════════════════════════════════════
with tab_facteurs:
    st.subheader("Météo vs urgences")
    if "temp_moy" in df.columns and col_y in df.columns:
        df_scatter = df[["temp_moy", "mois", "dept", col_y]].dropna()
        df_scatter["mois_label"] = df_scatter["mois"].apply(lambda m: MOIS_LABELS[m - 1])
        fig = px.scatter(
            df_scatter, x="temp_moy", y=col_y, color="mois_label",
            hover_data=["dept"], trendline="ols",
            labels={"temp_moy": "Température moyenne (°C)", col_y: "Part (/100k)", "mois_label": "Mois"},
            opacity=0.5, template="plotly_white", height=450,
        )
        st.plotly_chart(fig, width="stretch")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Pollen (saisonnalité nationale)")
        pollen_cols = [c for c in ["pollen_graminees_moy", "pollen_betula_moy", "pollen_ambrosia_moy"]
                      if c in df.columns]
        if pollen_cols and "taux_urgences_allergie" in df.columns:
            df_pol = df.groupby("mois")[pollen_cols + ["taux_urgences_allergie"]].mean().reindex(range(1, 13)).reset_index()
            df_pol["mois_label"] = df_pol["mois"].apply(lambda m: MOIS_LABELS[m - 1])
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            noms = {"pollen_graminees_moy": "Graminées", "pollen_betula_moy": "Bouleau", "pollen_ambrosia_moy": "Ambroisie"}
            for c in pollen_cols:
                fig.add_trace(go.Bar(x=df_pol["mois_label"], y=df_pol[c], name=noms[c], opacity=0.6), secondary_y=False)
            fig.add_trace(go.Scatter(x=df_pol["mois_label"], y=df_pol["taux_urgences_allergie"],
                                     name="Urgences Allergie", line=dict(color="#E74C3C", width=3),
                                     mode="lines+markers"), secondary_y=True)
            fig.update_layout(barmode="stack", template="plotly_white", height=420,
                              legend=dict(orientation="h", yanchor="bottom", y=1.02))
            fig.update_yaxes(title_text="Pollen (grains/m³)", secondary_y=False)
            fig.update_yaxes(title_text="Part urgences allergie (/100k)", secondary_y=True)
            st.plotly_chart(fig, width="stretch")

    with c2:
        st.subheader("Qualité de l'air (saisonnalité nationale)")
        air_cols = [c for c in ["pm10_moy", "no2_moy", "o3_moy"] if c in df.columns]
        if air_cols and "taux_urgences_asthme" in df.columns:
            df_air = df.groupby("mois")[air_cols + ["taux_urgences_asthme"]].mean().reindex(range(1, 13)).reset_index()
            df_air["mois_label"] = df_air["mois"].apply(lambda m: MOIS_LABELS[m - 1])
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            noms = {"pm10_moy": "PM10", "no2_moy": "NO₂", "o3_moy": "O₃"}
            for c in air_cols:
                fig.add_trace(go.Scatter(x=df_air["mois_label"], y=df_air[c], name=noms[c],
                                         line=dict(width=2, dash="dash"), mode="lines+markers"), secondary_y=False)
            fig.add_trace(go.Scatter(x=df_air["mois_label"], y=df_air["taux_urgences_asthme"],
                                     name="Urgences Asthme", line=dict(color="#2980B9", width=3),
                                     mode="lines+markers"), secondary_y=True)
            fig.update_layout(template="plotly_white", height=420,
                              legend=dict(orientation="h", yanchor="bottom", y=1.02))
            fig.update_yaxes(title_text="Concentration (µg/m³)", secondary_y=False)
            fig.update_yaxes(title_text="Part urgences asthme (/100k)", secondary_y=True)
            st.plotly_chart(fig, width="stretch")

# ═══════════════════════════════════════════════════════════════════════
# TAB 5 — Qualité des données (valeurs manquantes)
# ═══════════════════════════════════════════════════════════════════════
with tab_qualite:
    st.subheader("Taux de valeurs manquantes par variable")
    st.caption(
        "Calculé sur l'ensemble du dataset (`df_model`, non filtré par les sélections "
        "de la barre latérale) — vue globale de la complétude des données."
    )

    missing = (df_full.drop(columns=["annee_mois_dt"]).isnull().mean() * 100)
    missing = missing[missing > 0].sort_values(ascending=True)

    if missing.empty:
        st.success("✅ Aucune valeur manquante dans df_model.")
    else:
        bar_colors = [
            "#E74C3C" if v > 50 else "#F39C12" if v > 20 else "#27AE60"
            for v in missing.values
        ]
        fig = go.Figure(go.Bar(
            x=missing.values, y=missing.index, orientation="h",
            marker_color=bar_colors,
            hovertemplate="%{y}<br>%{x:.1f}%% manquant<extra></extra>",
        ))
        fig.add_vline(x=20, line_dash="dash", line_color="#F39C12",
                      annotation_text="20%", annotation_position="top")
        fig.add_vline(x=50, line_dash="dash", line_color="#E74C3C",
                      annotation_text="50%", annotation_position="top")
        fig.update_layout(
            title="Taux de valeurs manquantes (vert < 20% | orange 20-50% | rouge > 50%)",
            xaxis_title="% valeurs manquantes",
            template="plotly_white",
            height=max(400, len(missing) * 22),
        )
        st.plotly_chart(fig, width="stretch")

        st.info(
            "⚠️ Les colonnes `taux_sos_*` sont structurellement incomplètes (~53%) : "
            "le réseau SOS Médecins ne couvre pas tous les départements — ce n'est pas "
            "un défaut de collecte à corriger."
        )

# ═══════════════════════════════════════════════════════════════════════
# TAB 6 — Dictionnaire des données
# ═══════════════════════════════════════════════════════════════════════
with tab_dico:
    lignes = []
    for c in df_full.columns:
        if c in ("annee_mois_dt",):
            continue
        categorie, description, source = DICO_VARIABLES.get(c, ("?", "non documenté", "?"))
        lignes.append({
            "colonne": c, "categorie": categorie,
            "type": str(df_full[c].dtype), "description": description, "source": source,
        })
    df_dico = pd.DataFrame(lignes)

    cat_filtre = st.multiselect(
        "Filtrer par catégorie",
        sorted(df_dico["categorie"].unique()),
        default=[],
    )
    df_dico_affiche = df_dico[df_dico["categorie"].isin(cat_filtre)] if cat_filtre else df_dico

    st.dataframe(df_dico_affiche, width="stretch", height=600, hide_index=True)
    st.caption(f"{len(df_dico)} variables au total dans df_model.parquet")
