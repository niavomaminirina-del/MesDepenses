import streamlit as st
import requests
from datetime import date

st.set_page_config(page_title="MesDepenses")

url = "http://127.0.0.1:8000"

st.markdown("""
<style>
    [data-testid="stDecoration"] {
        display: none;
    }

    .stApp {
        background-color: white;
    }

    h1, h2, h3, p, label, span {
        color: black !important;
    }

    .stButton button,
    .stFormSubmitButton button {
        background-color: #70452F;
        color: white !important;
        border: none;
        border-radius: 0;
        box-shadow: none;
    }

    .stButton button:hover,
    .stFormSubmitButton button:hover {
        background-color: #70452F;
        color: white !important;
        border: none;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stDateInput input {
        background-color: white;
        color: black;
        border: 1px solid #70452F;
        border-radius: 0;
        box-shadow: none;
    }

    div[data-baseweb="select"] > div {
        background-color: white;
        color: black;
        border: 1px solid #70452F;
        border-radius: 0;
    }

    input:focus,
    textarea:focus {
        border: 1px solid #70452F !important;
        box-shadow: none !important;
    }

    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #70452F;
        padding: 10px;
        border-radius: 0;
    }

    [data-testid="stProgressBar"] > div > div {
        background-color: #70452F;
    }

    [data-testid="stDataFrame"] {
        border-radius: 0;
    }

    .stRadio {
        color: black;
    }

    .stRadio input {
        accent-color: #70452F;
    }
</style>
""", unsafe_allow_html=True)

st.title("MesDepenses")

menu = st.radio(
    "Navigation",
    ["Accueil", "Ajouter une dépense", "Mes dépenses", "Budget"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

if menu == "Accueil":

    st.header("Tableau de bord")

    try:
        stats = requests.get(url + "/budget/stats").json()

        col1, col2, col3 = st.columns(3)

        col1.metric("Budget initial", stats["budget_initial"], "Ar")
        col2.metric("Total des dépenses", stats["total_depenses"], "Ar")
        col3.metric("Solde restant", stats["solde_restant"], "Ar")

        st.write("Nombre de dépenses :", stats["nombre_depenses"])

        if stats["budget_initial"] > 0:
            pourcentage = stats["total_depenses"] / stats["budget_initial"]

            st.write("Budget utilisé :", round(pourcentage * 100, 2), "%")
            st.progress(min(pourcentage, 1.0))

        depenses = requests.get(url + "/depenses/").json()

        if depenses:
            st.subheader("Dépenses par catégorie")

            categories = {}

            for depense in depenses:
                nom_categorie = depense["categorie"]
                montant = depense["montant"]

                if nom_categorie in categories:
                    categories[nom_categorie] += montant
                else:
                    categories[nom_categorie] = montant

            st.bar_chart(categories)

    except requests.exceptions.RequestException:
        st.error("Impossible de contacter le serveur.")

elif menu == "Ajouter une dépense":

    st.header("Ajouter une dépense")

    titre = st.text_input("Titre")
    montant = st.number_input("Montant", min_value=0.0)
    categorie = st.text_input("Catégorie")
    date_depense = st.date_input("Date", value=date.today())
    description = st.text_area("Description")

    if st.button("Enregistrer"):

        if titre.strip() == "" or categorie.strip() == "" or montant <= 0:
            st.warning("Veuillez remplir les champs obligatoires.")

        else:
            nouvelle_depense = {
                "titre": titre,
                "montant": montant,
                "categorie": categorie,
                "date": str(date_depense),
                "description": description
            }

            try:
                resultat = requests.post(
                    url + "/depenses/",
                    json=nouvelle_depense
                )

                if resultat.status_code == 200:
                    st.success("Dépense ajoutée.")
                    st.rerun()
                else:
                    st.error("Erreur lors de l'ajout.")

            except requests.exceptions.RequestException:
                st.error("Serveur inaccessible.")

elif menu == "Mes dépenses":

    st.header("Mes dépenses")

    try:
        resultat = requests.get(url + "/depenses/")
        depenses = resultat.json()

        if depenses:

            st.dataframe(depenses)

            liste_ids = []

            for depense in depenses:
                liste_ids.append(depense["id"])

            id_choisi = st.selectbox("Choisir une dépense", liste_ids)

            depense_choisie = None

            for depense in depenses:
                if depense["id"] == id_choisi:
                    depense_choisie = depense

            with st.form("modifier_depense"):

                titre = st.text_input(
                    "Titre",
                    value=depense_choisie["titre"]
                )

                montant = st.number_input(
                    "Montant",
                    min_value=0.0,
                    value=float(depense_choisie["montant"])
                )

                categorie = st.text_input(
                    "Catégorie",
                    value=depense_choisie["categorie"]
                )

                date_depense = st.date_input(
                    "Date",
                    value=date.fromisoformat(depense_choisie["date"])
                )

                description = st.text_area(
                    "Description",
                    value=depense_choisie["description"] or ""
                )

                modifier = st.form_submit_button("Modifier")

                if modifier:

                    depense_modifiee = {
                        "titre": titre,
                        "montant": montant,
                        "categorie": categorie,
                        "date": str(date_depense),
                        "description": description
                    }

                    resultat = requests.put(
                        url + "/depenses/" + str(id_choisi),
                        json=depense_modifiee
                    )

                    if resultat.status_code == 200:
                        st.success("Dépense modifiée.")
                        st.rerun()
                    else:
                        st.error("Erreur de modification.")

            if st.button("Supprimer"):

                resultat = requests.delete(
                    url + "/depenses/" + str(id_choisi)
                )

                if resultat.status_code == 200:
                    st.success("Dépense supprimée.")
                    st.rerun()
                else:
                    st.error("Erreur de suppression.")

        else:
            st.info("Aucune dépense enregistrée.")

    except requests.exceptions.RequestException:
        st.error("Impossible de contacter le serveur.")

elif menu == "Budget":

    st.header("Gestion du budget")

    try:
        resultat = requests.get(url + "/budget/")
        budget = resultat.json()

        budget_actuel = budget["montant"]

        if budget_actuel is None:
            budget_actuel = 0.0

        st.write("Budget actuel :", budget_actuel, "Ar")

        nouveau_budget = st.number_input(
            "Nouveau budget",
            min_value=0.0,
            value=float(budget_actuel)
        )

        if st.button("Enregistrer"):

            donnees = {
                "montant": nouveau_budget
            }

            resultat = requests.put(
                url + "/budget/",
                json=donnees
            )

            if resultat.status_code == 200:
                st.success("Budget enregistré.")
                st.rerun()
            else:
                st.error("Erreur lors de l'enregistrement.")

    except requests.exceptions.RequestException:
        st.error("Impossible de contacter le serveur.")