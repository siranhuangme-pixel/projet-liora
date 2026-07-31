"""
Validation partagée pour les tables dim_* produites indépendamment par chaque
membre de l'équipe. À appeler juste avant de sauvegarder un dim_*.parquet,
pour repérer les problèmes de clé de jointure AVANT la fusion finale
(02_merge_final.ipynb) plutôt qu'après.
"""
import pandas as pd

from .config import DEPTS


def valider_dim_table(df: pd.DataFrame, nom: str, cle: list = None) -> bool:
    """
    Vérifie qu'une table dim_* est prête à être jointe à fact_urgences.

    Contrôles effectués :
    - la colonne "dept" existe et ses valeurs sont toutes dans DEPTS
    - pas de doublon sur la clé (par défaut ["dept"], ou ["dept", "annee_mois"]
      / ["dept", "annee"] si l'une de ces colonnes est présente)
    - taux de valeurs manquantes par colonne (affiché, non bloquant)

    Retourne True si aucun problème bloquant n'est détecté (à corriger sinon,
    avant de fournir le fichier pour la fusion finale).
    """
    ok = True
    print(f"── Validation de {nom} ──")

    if "dept" not in df.columns:
        print("  ❌ Colonne 'dept' absente")
        return False

    depts_invalides = set(df["dept"].unique()) - set(DEPTS)
    if depts_invalides:
        print(f"  ❌ Codes départements hors DEPTS : {sorted(depts_invalides)}")
        ok = False
    else:
        print(f"  ✅ Tous les codes dept sont valides ({df['dept'].nunique()} départements)")

    if cle is None:
        if "annee_mois" in df.columns:
            cle = ["dept", "annee_mois"]
        elif "annee" in df.columns:
            cle = ["dept", "annee"]
        else:
            cle = ["dept"]

    doublons = int(df.duplicated(subset=cle).sum())
    if doublons:
        print(f"  ❌ {doublons} doublons sur la clé {cle}")
        ok = False
    else:
        print(f"  ✅ Aucun doublon sur la clé {cle}")

    missing = (df.isnull().mean() * 100).round(1)
    missing = missing[missing > 0]
    if not missing.empty:
        print("  Taux de valeurs manquantes :")
        for col, pct in missing.items():
            print(f"    {col:<30} {pct:>5.1f}%")

    print(f"  {'✅ OK — prêt pour la fusion' if ok else '⚠️  À corriger avant la fusion'} ({nom})\n")
    return ok
