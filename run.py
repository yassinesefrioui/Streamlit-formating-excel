import streamlit as st
import pandas as pd
import re

def split_address_safe(address):
    if not isinstance(address, str) or pd.isna(address) or address.strip() == '':
        return pd.Series([None, None, None, None, None])
    address_parts = address.split()
    adresse1 = " ".join(address_parts[:min(100, len(address_parts))])
    adresse2 = None
    cp = commune = pays = None
    if len(address_parts) > 100:
        adresse2 = " ".join(address_parts[100:])
    match = re.search(r"(\d{5})\s+(.*)\s+(.*)$", address)
    if match:
        cp, commune, pays = match.groups()
    return pd.Series([
        adresse1[:100],
        adresse2[:75] if adresse2 else None,
        cp[:9] if cp else None,
        commune[:55] if commune else None,
        pays,
    ])

def truncate(value, max_length):
    if pd.isna(value):
        return value
    return str(value)[:max_length]

def transform_code(code):
    if pd.isna(code):
        return code
    code = str(code)
    if code.startswith('0') or code.startswith('9'):
        code = code[1:]
    elif code.startswith('CLT') or code.startswith('FRS'):
        code = code[3:]
        if code.startswith('0'):
            code = code[1:]
    return code[:7]

def standardize_excel(df):
    df[['Adresse1', 'Adresse2', 'Code postal', 'Commune', 'Pays']] = df['Adresse'].apply(split_address_safe)
    df = df.drop(columns=['Adresse'])

    df['Code'] = df['Code'].apply(transform_code)
    df['Nom'] = df['Nom'].apply(lambda x: truncate(x, 40))
    df['Email'] = df['Email'].apply(lambda x: truncate(x, 90))
    df['Téléphone'] = df['Téléphone'].apply(lambda x: truncate(x, 15))

    columns_constraints = {
        'Famille': 5,
        'Situation_TVA': 1,
        'Facturation': 5,
        'Titre': 5,
        'Titre_Lib': 30,
        'Ville_Rcs': 30,
        'Capital_Social': 30,
        'Nom':40,
        'Representant_Nom':40,
        'Prenom': 30,
        'Depot_Nom': 30,
        'Tel_Fixe': 15,
        'Tel_Mobile': 15,
        'Fax': 15,
        'Pays_Taxation': 2,
        'Categorie_Tarifaire': 5,
        'Delais_Reglement': 5,
        'Mode_Reglement': 5,
        'Ristourne_Pied': 15,
        'Remise_Ligne': 15,
        'Encours_Autorise': 15,
        'Taux': 15,
        'Nr_TVA_intracommunautaire': 15,
        'Representant': 7,
        'Depot': 7,
        'Parrain': 7,
        'Comite_Entreprise_Code': 7,
        'Date_Creation': 10,
        'Entreprise_Nr_Siret': 14,
        'Entreprise_Nr_Siren': 20,
        'Site_Internet': 100,
        'Visibilité': 1,
        'Bloc_Notes': 1000
    }

    for column, max_length in columns_constraints.items():
        if column in df.columns:
            df[column] = df[column].apply(lambda x: truncate(x, max_length))

    return df

def main():
    st.title("Transformation automatique des colonnes pour permettre l'importation dans GC")

    # Chargement du fichier
    uploaded_file = st.file_uploader("Veuillez uploader un fichier Excel", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            # Lecture du fichier Excel
            df = pd.read_excel(uploaded_file)

            # Affichage des données
            st.success("Fichier chargé avec succès ! Voici un aperçu des données :")
            st.dataframe(df)

            # Traitement des données avec standardize_excel
            df_transformed = standardize_excel(df)

            # Télécharger le fichier traité
            @st.cache_data
            def convert_df_to_excel(df):
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Feuille1")
                return output.getvalue()

            st.download_button(
                label="Télécharger le fichier transformé",
                data=convert_df_to_excel(df_transformed),
                file_name="fichier_transforme.xlsx"
            )

        except Exception as e:
            st.error(f"Erreur lors de la lecture ou du traitement du fichier : {e}")

if __name__ == "__main__":
    main()
