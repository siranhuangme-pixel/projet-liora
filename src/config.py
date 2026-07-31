"""
Configuration partagée du pipeline de données — Projet Liora.

Toutes les notebooks (00_config_commun, 01x_pipeline_*, 02_merge_final)
doivent importer ces mêmes constantes plutôt que de les redéfinir, pour que
les clés de jointure (dept, annee_mois) soient garanties identiques entre
les tables produites indépendamment par chaque membre de l'équipe.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# RAW_DIR : par défaut data/raw/ du projet, mais surchargeable par personne
# via une variable d'environnement (ex : données stockées ailleurs sur son
# poste). Ne rien définir = comportement inchangé pour tout le monde.
#   export LIORA_RAW_DIR=/chemin/vers/mes/donnees
RAW_DIR = Path(os.environ.get("LIORA_RAW_DIR", PROJECT_ROOT / "data" / "raw"))
TABLES_DIR = PROJECT_ROOT / "data" / "processed"
for _d in (RAW_DIR, TABLES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

ANNEE_DEBUT = 2020
ANNEE_FIN = 2025

# ⚠️ Corse : toujours 2A/2B, jamais "20" (cf. notebooks dim_meteo / dim_qualite_air
# pour la logique de scission des sources qui livrent un code "20" unique).
DEPTS = [f"{i:02d}" for i in range(1, 96) if i != 20] + ["2A", "2B"]
# Décommentez pour inclure les DOM :
# DEPTS += ["971", "972", "973", "974", "976"]

# Nom département (tel que renvoyé par reverse_geocoder, champ "admin2") → code INSEE. 
# Utilisé par tout pipeline qui géocode des coordonnées lat/lon pour retrouver le département (ex : dim_meteo, dim_qualite_air).
# Source Code INSEE vs. Nom de département : https://www.insee.fr/fr/information/8377162

DEPT_NOM_TO_CODE = {
    "Departement de l'Ain": "01", "Departement de l'Aisne": "02",
    "Departement de l'Allier": "03", "Departement des Alpes-de-Haute-Provence": "04",
    "Departement des Hautes-Alpes": "05",
    "Departement des Alpes-Maritimes": "06", "Departement de l'Ardeche": "07",
    "Departement des Ardennes": "08", "Departement de l'Ariege": "09",
    "Departement de l'Aube": "10", "Departement de l'Aude": "11",
    "Departement de l'Aveyron": "12", "Departement des Bouches-du-Rhone": "13",
    "Departement du Calvados": "14", "Departement du Cantal": "15",
    "Departement de la Charente": "16", "Departement de la Charente-Maritime": "17",
    "Departement du Cher": "18", "Departement de la Correze": "19",
    "Departement de la Cote-d'Or": "21", "Departement des Cotes-d'Armor": "22",
    "Departement de la Creuse": "23", "Departement de la Dordogne": "24",
    "Departement du Doubs": "25", "Departement de la Drome": "26",
    "Departement de l'Eure": "27", "Departement d'Eure-et-Loir": "28",
    "Departement du Finistere": "29", "Departement du Gard": "30",
    "Departement de la Haute-Garonne": "31", "Departement du Gers": "32",
    "Departement de la Gironde": "33", "Departement de l'Herault": "34",
    "Departement d'Ille-et-Vilaine": "35", "Departement de l'Indre": "36",
    "Departement d'Indre-et-Loire": "37", "Departement de l'Isere": "38",
    "Departement du Jura": "39", "Departement des Landes": "40",
    "Departement du Loir-et-Cher": "41", "Departement de la Loire": "42",
    "Departement de la Haute-Loire": "43", "Departement de la Loire-Atlantique": "44",
    "Departement du Loiret": "45", "Departement du Lot": "46",
    "Departement du Lot-et-Garonne": "47", "Departement de la Lozere": "48",
    "Departement du Maine-et-Loire": "49", "Departement de la Manche": "50",
    "Departement de la Marne": "51", "Departement de la Haute-Marne": "52",
    "Departement de la Mayenne": "53", "Departement de Meurthe-et-Moselle": "54",
    "Departement de la Meuse": "55", "Departement du Morbihan": "56",
    "Departement de la Moselle": "57", "Departement de la Nievre": "58",
    "Departement du Nord": "59", "Departement de l'Oise": "60",
    "Departement de l'Orne": "61", "Departement du Pas-de-Calais": "62",
    "Departement du Puy-de-Dome": "63", "Departement des Pyrenees-Atlantiques": "64",
    "Departement des Hautes-Pyrenees": "65", "Departement des Pyrenees-Orientales": "66",
    "Departement du Bas-Rhin": "67", "Departement du Haut-Rhin": "68",
    "Departement du Rhone": "69", "Departement de la Haute-Saone": "70",
    "Departement de Saone-et-Loire": "71", "Departement de la Sarthe": "72",
    "Departement de la Savoie": "73", "Departement de la Haute-Savoie": "74",
    "Departement de Paris": "75", "Departement de la Seine-Maritime": "76",
    "Departement de Seine-et-Marne": "77", "Departement des Yvelines": "78",
    "Departement des Deux-Sevres": "79", "Departement de la Somme": "80",
    "Departement du Tarn": "81", "Departement du Tarn-et-Garonne": "82",
    "Departement du Var": "83", "Departement du Vaucluse": "84",
    "Departement de la Vendee": "85", "Departement de la Vienne": "86",
    "Departement de la Haute-Vienne": "87", "Departement des Vosges": "88",
    "Departement de l'Yonne": "89", "Departement du Territoire de Belfort": "90",
    "Departement de l'Essonne": "91", "Departement des Hauts-de-Seine": "92",
    "Departement de la Seine-Saint-Denis": "93", "Departement du Val-de-Marne": "94",
    "Departement du Val-d'Oise": "95",
    "Departement de la Corse-du-Sud": "2A", "Departement de la Haute-Corse": "2B",

    # (mêmes départements, formulation différente selon l'entrée géographique) :
    "Paris": "75",
    "Departement de Seine-Saint-Denis": "93",
    "Departement de Maine-et-Loire": "49",
    "Territoire de Belfort": "90",
}
