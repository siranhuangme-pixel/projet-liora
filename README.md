# Prédiction du taux d'incidence — allergie / asthme / bronchiolite

Projet DataScientest / Liora — Direction de l'Actuariat Vie (CAAS)

Construction d'un dataset mensuel par département (2020-2025) croisant les
passages aux urgences (allergie, asthme, bronchiolite) avec des facteurs
météorologiques, environnementaux, démographiques et socio-économiques, en
vue d'une modélisation prédictive.

## Structure du projet

```
├── README.md
├── requirements.txt
├── app.py                  <- Dashboard interactif Streamlit (streamlit run app.py)
├── .streamlit/             <- Configuration du thème Streamlit
│
├── data
│   ├── raw                 <- Données brutes téléchargées manuellement (non versionnées)
│   └── processed           <- Tables construites par le pipeline (.parquet)
│
├── notebooks
│   ├── 00_config_commun.ipynb       <- Config partagée (DEPTS, chemins) + dim_temps + fact_urgences (Y)
│   ├── 01a_pipeline_meteo.ipynb     <- dim_meteo (Météo France)
│   ├── 01b_pipeline_geo_pop.ipynb   <- dim_geo_pop (INSEE + Ameli)
│   ├── 01c_pipeline_csp.ipynb       <- dim_csp (INSEE CSP)
│   ├── 01d_pipeline_qualite_air.ipynb <- dim_qualite_air (LCSQA/AASQA)
│   ├── 01e_pipeline_pollen.ipynb    <- dim_pollen (RNSA)
│   ├── 01f_pipeline_medecins.ipynb  <- dim_medecins (DREES RPPS, dept x année)
│   ├── 01g_pipeline_indicateurs_contexte.ipynb <- dim_indicateurs_contexte (DREES ISD, dept x année)
│   ├── 01h_pipeline_etablissements_sante.ipynb <- dim_etablissements_sante (FINESS, dept x année)
│   ├── 01i_pipeline_incendies.ipynb <- dim_incendies (BDIFF, dept x année-mois)
│   ├── 01x_pipeline_template.ipynb  <- Template à copier pour ajouter une nouvelle source
│   ├── 02_merge_final.ipynb         <- Fusion automatique fact_urgences + tous les dim_*.parquet -> df_model
│   ├── 03_eda.ipynb                 <- Analyse exploratoire / visualisation (pas de nettoyage)
│   ├── 04_nettoyage_donnees.ipynb   <- Imputation -> df_model_clean, prêt pour la modélisation
│   └── old/01_data_pipeline_monolithique.ipynb <- Ancienne version tout-en-un (référence/historique)
│
├── reports
│   └── figures             <- Graphiques exportés (HTML interactifs)
│
├── references              <- Documents du projet Liora + dictionnaire_donnees.csv
│
├── models                  <- Modèles entraînés (à venir)
│
└── src                     <- Squelette pour du code réutilisable (features/models/visualization)
```

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

Le pipeline est découpé pour permettre à chaque membre de l'équipe de
construire sa propre table de façon indépendante (voir `src/config.py` et
`src/validation.py` pour la configuration et la validation partagées) :

1. **Télécharger les données brutes** dans `data/raw/` — voir les instructions
   au début de chaque section des notebooks `01x_pipeline_*.ipynb` (sources,
   URLs, format attendu).
2. **Exécuter `notebooks/00_config_commun.ipynb`** en premier — construit
   `dim_temps` et `fact_urgences` (nos 3 variables cibles Y), et fournit la
   configuration partagée (`DEPTS`, chemins, années).
3. **Chacun exécute son(ses) propre(s) notebook(s) `01x_pipeline_*.ipynb`**
   (météo / géo-population / CSP / qualité de l'air / pollen / médecins /
   indicateurs de contexte / établissements de santé / incendies) —
   indépendamment des autres, dans l'ordre de son choix. Chaque notebook
   valide sa table avant de la sauvegarder (`valider_dim_table`, cf.
   `src/validation.py`) et produit un `dim_xxx.parquet` dans
   `data/processed/`. Les tables annuelles (`dim_medecins`,
   `dim_indicateurs_contexte`, `dim_etablissements_sante` — clé `dept` +
   `annee`, pas `annee_mois`) sont automatiquement diffusées sur les 12 mois
   de l'année correspondante lors de la fusion.

   **Pour ajouter une nouvelle source de données**, dupliquer
   `notebooks/01x_pipeline_template.ipynb` sous un nouveau nom
   (`01j_pipeline_<nom>.ipynb`) et suivre les instructions en tête du
   notebook. Aucune autre modification n'est nécessaire ailleurs : il suffit
   que le fichier produit s'appelle `dim_<nom>.parquet` avec une colonne
   `dept` (+ `annee_mois` ou `annee` selon la maille).

4. **Exécuter `notebooks/02_merge_final.ipynb`** — découvre automatiquement
   toutes les tables `dim_*.parquet` présentes dans `data/processed/` et les
   fusionne à `fact_urgences` → `data/processed/df_model.parquet`. Pas besoin
   de modifier ce notebook quand une nouvelle table `dim_*` est ajoutée.
5. **Exécuter `notebooks/03_eda.ipynb`** — exploration et visualisation
   uniquement (dictionnaire de données, tendances, corrélations).
6. **Exécuter `notebooks/04_nettoyage_donnees.ipynb`** — imputation des
   valeurs manquantes, produit `data/processed/df_model_clean.parquet`,
   prêt pour la modélisation.
7. **Lancer le dashboard interactif** :
   ```bash
   streamlit run app.py
   ```

> `notebooks/old/01_data_pipeline_monolithique.ipynb` contient l'ancienne version
> tout-en-un (avant ce découpage) — conservée comme référence/historique,
> mais ce n'est plus la version à faire évoluer.

## Sources de données

| Domaine                                                      | Source                                   |
| ------------------------------------------------------------ | ---------------------------------------- |
| Urgences (Y)                                                 | Santé Publique France (Odissé)           |
| Météo                                                        | Météo France (données mensuelles MENSQ)  |
| Qualité de l'air                                             | LCSQA / AASQA                            |
| Pollen & moisissures                                         | RNSA                                     |
| Démographie & pathologies                                    | CNAM (Cartographie des pathologies)      |
| Urbanisation, CSP                                            | INSEE                                    |
| Densité médicale (statique, moyenne 2020-2024)               | Ameli                                    |
| Densité de médecins (par année)                              | DREES RPPS                               |
| Indicateurs de contexte (vieillissement, activité, CSP...)   | DREES ISD                                |
| Établissements de santé (hôpitaux, pharmacies, laboratoires) | FINESS                                   |
| Incendies de forêt (nombre, surface parcourue)               | BDIFF (Ministère de l'Agriculture / IGN) |

Le détail de chaque source, les bugs corrigés et les limites connues sont
documentés dans le notebook markdown de chaque section `01x_pipeline_*.ipynb`.

## Schéma en étoile

Chaque `01x_pipeline_*.ipynb` construit sa table indépendamment ; `02_merge_final.ipynb`
les découvre et les fusionne à `fact_urgences` sur la clé disponible (`dept`,
`dept + annee_mois`, ou `dept + annee` — diffusée sur les 12 mois de l'année).
Le détail des colonnes de `df_model` (source, maille, description) est dans
`references/dictionnaire_donnees.csv`.
