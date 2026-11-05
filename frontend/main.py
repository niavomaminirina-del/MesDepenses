
from datetime import date

import requests

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# ==============================
# CONFIGURATION
# ==============================

API_URL = "http://127.0.0.1:8000"
DELAI_API = 5  # secondes avant abandon d'une requête

# ==============================
# THEME DE L'APPLICATION
# ==============================

FOND = (1, 0.99, 0.97, 1)            # blanc cassé (fond général)
BLANC = (1, 1, 1, 1)
ROSE = (0.94, 0.79, 0.82, 1)         # boutons / éléments importants
ROSE_CLAIR = (0.98, 0.89, 0.91, 1)
ROSE_FONCE = (0.55, 0.32, 0.39, 1)   # titres
ROSE_VIF = (0.88, 0.60, 0.67, 1)     # barre de progression
JAUNE = (0.96, 0.91, 0.66, 1)        # informations à mettre en évidence
VERT = (0.79, 0.87, 0.79, 1)         # validations / réussites
CARTE_NEUTRE = (0.98, 0.95, 0.94, 1)
CONTOUR = (0.91, 0.85, 0.87, 1)      # contour fin des cartes et des champs
FOND_CHAMP = (0.99, 0.98, 0.97, 1)

TEXTE = (0.30, 0.27, 0.28, 1)        # gris foncé doux
TEXTE_DOUX = (0.50, 0.46, 0.47, 1)
TEXTE_PLACEHOLDER = (0.65, 0.62, 0.63, 1)
SUCCES = (0.28, 0.48, 0.31, 1)       # texte des messages de réussite
ERREUR = (0.72, 0.30, 0.36, 1)       # texte des messages d'erreur


# Formes : rayons des coins [haut-gauche, haut-droit, bas-droit, bas-gauche]
FORME_A = [30, 6, 30, 6]
FORME_B = [6, 30, 6, 30]


def convertir_rayon(rayon):
    """Accepte un rayon unique ou une liste de 4 rayons, et applique dp()."""
    if isinstance(rayon, (list, tuple)):
        return [dp(valeur) for valeur in rayon]
    return [dp(rayon)]


def assombrir(couleur, facteur=0.8):
    """Version plus foncée d'une couleur (pour les contours)."""
    r, g, b, a = couleur
    return (r * facteur, g * facteur, b * facteur, a)


def geometrie_contour(widget, rayons):
    """Paramètres de Line.rounded_rectangle pour un widget (rayons limités à la taille)."""
    x, y = widget.pos
    largeur, hauteur = widget.size
    maximum = max(0, min(largeur, hauteur) / 2)
    return (x, y, largeur, hauteur, *[min(rayon, maximum) for rayon in rayons])


# ==============================
# COMMUNICATION AVEC L'API
# ==============================

class ErreurAPI(Exception):
    """Erreur lisible par l'utilisateur (connexion, réponse du serveur...)."""


def _detail_erreur(reponse):
    """Extrait un message lisible d'une réponse d'erreur FastAPI."""
    if reponse is None:
        return "Erreur de communication avec le serveur."
    try:
        detail = reponse.json().get("detail")
    except (ValueError, AttributeError):
        detail = None
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return "Le serveur a refusé les données envoyées."
    return f"Erreur du serveur (code {reponse.status_code})."


def requete_api(methode, chemin, **kwargs):
    """
    Envoie une requête à l'API et retourne le JSON reçu (ou None si la
    réponse est vide). Lève ErreurAPI avec un message clair en cas de problème.
    """
    try:
        reponse = requests.request(
            methode,
            f"{API_URL}{chemin}",
            timeout=DELAI_API,
            **kwargs
        )
        reponse.raise_for_status()
    except requests.HTTPError as erreur:
        raise ErreurAPI(_detail_erreur(erreur.response))
    except requests.Timeout:
        raise ErreurAPI("Le serveur met trop de temps à répondre.")
    except requests.ConnectionError:
        raise ErreurAPI(
            "Impossible de joindre le serveur. Vérifie que l'API est lancée."
        )
    except requests.RequestException:
        raise ErreurAPI("Erreur de communication avec le serveur.")

    try:
        return reponse.json()
    except ValueError:
        return None


# Une fonction par route utilisée (routes identiques à l'ancien code)

def api_stats():
    return requete_api("GET", "/budget/stats")


def api_enregistrer_budget(montant):
    return requete_api("PUT", "/budget/", json={"montant": montant})


def api_lister_depenses():
    return requete_api("GET", "/depenses/")


def api_creer_depense(donnees):
    return requete_api("POST", "/depenses/", json=donnees)


def api_modifier_depense(id_depense, donnees):
    return requete_api("PUT", f"/depenses/{id_depense}", json=donnees)


def api_supprimer_depense(id_depense):
    return requete_api("DELETE", f"/depenses/{id_depense}")


# ==============================
# OUTILS DIVERS
# ==============================

def formater_montant(valeur):
    """1500000 -> '1 500 000 Ar'."""
    return f"{float(valeur):,.0f}".replace(",", " ") + " Ar"


def montant_en_texte(valeur):
    """Montant pour un champ de saisie : 1500.0 -> '1500'."""
    valeur = float(valeur)
    return str(int(valeur)) if valeur.is_integer() else str(valeur)


# ==============================
# WIDGETS PERSONNALISES
# ==============================

class Carte(BoxLayout):
    """
    Conteneur vertical à coins personnalisables, hauteur automatique.
    Options : contour fin coloré (contour) et petite barre d'accent à gauche (accent).
    """

    def __init__(self, couleur=CARTE_NEUTRE, rayon=18, contour=None, accent=None, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("padding", dp(12))
        kwargs.setdefault("spacing", dp(4))
        super().__init__(**kwargs)

        self._rayons = convertir_rayon(rayon)
        self._contour = contour
        self._accent = accent

        with self.canvas.before:
            Color(*couleur)
            self._fond = RoundedRectangle(
                pos=self.pos, size=self.size, radius=self._rayons
            )
            if contour:
                Color(*contour)
                self._ligne = Line(
                    rounded_rectangle=geometrie_contour(self, self._rayons),
                    width=dp(1.4)
                )
            if accent:
                Color(*accent)
                self._barre = RoundedRectangle(
                    pos=self.pos, size=(dp(4), dp(10)), radius=[dp(2)]
                )

        self.bind(pos=self._maj_fond, size=self._maj_fond)
        self.bind(minimum_height=self.setter("height"))

    def _maj_fond(self, *args):
        self._fond.pos = self.pos
        self._fond.size = self.size
        if self._contour:
            self._ligne.rounded_rectangle = geometrie_contour(self, self._rayons)
        if self._accent:
            self._barre.pos = (self.x + dp(10), self.y + dp(10))
            self._barre.size = (dp(4), max(0, self.height - dp(20)))


class Texte(Label):
    """Label aligné à gauche, qui retourne à la ligne et ajuste sa hauteur."""

    def __init__(self, **kwargs):
        kwargs.setdefault("color", TEXTE)
        kwargs.setdefault("halign", "left")
        kwargs.setdefault("valign", "middle")
        kwargs.setdefault("font_size", sp(16))
        kwargs.setdefault("size_hint_y", None)
        super().__init__(**kwargs)
        self.bind(
            width=self._maj_largeur,
            texture_size=self._maj_hauteur,
            text=self._maj_hauteur
        )
        self._maj_hauteur()  # évite la hauteur par défaut (100) d'un texte vide

    def _maj_largeur(self, *args):
        self.text_size = (self.width, None)

    def _maj_hauteur(self, *args):
        # Un texte vide ne prend aucune place
        self.height = self.texture_size[1] + dp(4) if self.text else 0


class Message(Texte):
    """Texte de retour utilisateur : vert pour une réussite, rouge doux sinon."""

    def __init__(self, **kwargs):
        kwargs.setdefault("font_size", sp(15))
        super().__init__(**kwargs)

    def afficher(self, texte, succes=True):
        self.color = SUCCES if succes else ERREUR
        self.text = texte

    def effacer(self):
        self.text = ""


class BoutonPastel(Button):
    """
    Bouton de couleur pastel.
    style="plein"    : fond coloré
    style="contour"  : fond blanc, contour coloré (se remplit quand on appuie)
    rayon            : rayon des coins (23 = forme de pilule pour un bouton de 46)
    """

    def __init__(self, couleur=ROSE, rayon=14, style="plein", **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        kwargs.setdefault("color", TEXTE)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("font_size", sp(15))
        super().__init__(
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            **kwargs
        )

        self._couleur = couleur
        self._style = style
        self._rayons = convertir_rayon(rayon)

        with self.canvas.before:
            self._teinte = Color(*(BLANC if style == "contour" else couleur))
            self._fond = RoundedRectangle(
                pos=self.pos, size=self.size, radius=self._rayons
            )
            if style == "contour":
                Color(*assombrir(couleur, 0.8))
                self._ligne = Line(
                    rounded_rectangle=geometrie_contour(self, self._rayons),
                    width=dp(1.6)
                )

        self.bind(pos=self._maj_fond, size=self._maj_fond, state=self._maj_etat)

    def _maj_fond(self, *args):
        self._fond.pos = self.pos
        self._fond.size = self.size
        if self._style == "contour":
            self._ligne.rounded_rectangle = geometrie_contour(self, self._rayons)

    def _maj_etat(self, *args):
        appuye = self.state == "down"
        if self._style == "contour":
            self._teinte.rgba = self._couleur if appuye else BLANC
        else:
            self._teinte.rgba = assombrir(self._couleur, 0.9 if appuye else 1)


class ChampTexte(BoxLayout):
    """
    Champ de saisie monoligne sur fond blanc arrondi.
    Le fond arrondi est dessiné par ce conteneur, et la saisie est faite dans
    un TextInput transparent (le texte reste ainsi toujours visible).
    Utilisation : champ.text pour lire ou modifier le contenu.
    """

    def __init__(self, hint_text="", input_filter=None, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(42))
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*FOND_CHAMP)
            self._fond = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(10)]
            )
            self._couleur_ligne = Color(*CONTOUR)
            self._ligne = Line(
                rounded_rectangle=geometrie_contour(self, [dp(10)]),
                width=dp(1.4)
            )
        self.bind(pos=self._maj_fond, size=self._maj_fond)

        self.saisie = TextInput(
            hint_text=hint_text,
            input_filter=input_filter,
            multiline=False,
            font_size=sp(15),
            padding=[dp(14), dp(10), dp(14), dp(10)],
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=TEXTE,
            hint_text_color=TEXTE_PLACEHOLDER,
            cursor_color=ROSE_FONCE,
            write_tab=False
        )
        self.add_widget(self.saisie)

        # Le contour devient rose foncé quand le champ est actif
        self.saisie.bind(focus=self._maj_focus)

    def _maj_focus(self, instance, actif):
        self._couleur_ligne.rgba = ROSE_FONCE if actif else CONTOUR

    def _maj_fond(self, *args):
        self._fond.pos = self.pos
        self._fond.size = self.size
        self._ligne.rounded_rectangle = geometrie_contour(self, [dp(10)])

    @property
    def text(self):
        return self.saisie.text

    @text.setter
    def text(self, valeur):
        self.saisie.text = valeur


class BarreProgression(Widget):
    """Barre de progression arrondie (valeur entre 0 et 1)."""

    def __init__(self, couleur=ROSE_VIF, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(10))
        super().__init__(**kwargs)

        self.valeur = 0

        with self.canvas:
            Color(*BLANC)
            self._piste = RoundedRectangle(radius=[dp(5)])
            Color(*couleur)
            self._remplissage = RoundedRectangle(radius=[dp(5)])

        self.bind(pos=self._maj, size=self._maj)

    def definir(self, valeur):
        self.valeur = max(0, min(1, valeur))
        self._maj()

    def _maj(self, *args):
        self._piste.pos = self.pos
        self._piste.size = self.size
        self._remplissage.pos = self.pos
        self._remplissage.size = (self.width * self.valeur, self.height)


JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def date_du_jour_texte():
    """Ex. : 'Jeudi 5 novembre 2026'."""
    aujourdhui = date.today()
    return (
        f"{JOURS[aujourdhui.weekday()].capitalize()} {aujourdhui.day} "
        f"{MOIS[aujourdhui.month - 1]} {aujourdhui.year}"
    )


def carte_formulaire():
    """Carte blanche à contour fin pour les formulaires."""
    return Carte(couleur=BLANC, rayon=14, contour=CONTOUR, padding=dp(14))


def ligne_horizontale(**kwargs):
    """Ligne horizontale dont la hauteur s'adapte à son contenu."""
    ligne = BoxLayout(orientation="horizontal", size_hint_y=None, **kwargs)
    ligne.bind(minimum_height=ligne.setter("height"))
    return ligne


# ==============================
# FORMULAIRE DE DEPENSE (réutilisé pour l'ajout et la modification)
# ==============================

class FormulaireDepense(BoxLayout):
    """Champs d'une dépense + bouton d'enregistrement + message de retour."""

    def __init__(self, texte_bouton, action, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))

        self.champ_titre = ChampTexte(hint_text="Titre de la dépense")
        self.champ_montant = ChampTexte(
            hint_text="Montant en Ariary",
            input_filter="float"
        )
        self.champ_categorie = ChampTexte(hint_text="Catégorie")
        self.champ_description = ChampTexte(
            hint_text="Description (facultative)"
        )
        self.label_date = Texte(color=TEXTE_DOUX, font_size=sp(14))
        self.bouton = BoutonPastel(text=texte_bouton, couleur=VERT, rayon=23)
        self.message = Message()

        self.bouton.bind(on_press=lambda instance: action())

        for widget in (
            self.champ_titre,
            self.champ_montant,
            self.champ_categorie,
            self.champ_description,
            self.label_date,
            self.bouton,
            self.message,
        ):
            self.add_widget(widget)

        self.vider()

    def vider(self):
        """Remet le formulaire à zéro (mode ajout, date du jour)."""
        self.champ_titre.text = ""
        self.champ_montant.text = ""
        self.champ_categorie.text = ""
        self.champ_description.text = ""
        self.label_date.text = f"Date : {date.today().isoformat()}"
        self.message.effacer()

    def remplir(self, depense):
        """Charge une dépense existante (mode modification)."""
        self.champ_titre.text = depense.get("titre") or ""
        self.champ_montant.text = montant_en_texte(depense.get("montant") or 0)
        self.champ_categorie.text = depense.get("categorie") or ""
        self.champ_description.text = depense.get("description") or ""
        self.label_date.text = f"Date : {depense.get('date', '')}"
        self.message.effacer()

    def lire_donnees(self, date_depense):
        """
        Valide les champs et retourne le dictionnaire JSON attendu par l'API,
        ou None (avec un message d'erreur affiché) si la saisie est invalide.
        """
        titre = self.champ_titre.text.strip()
        categorie = self.champ_categorie.text.strip()

        if not titre or not self.champ_montant.text.strip() or not categorie:
            self.message.afficher("Remplis les champs obligatoires.", False)
            return None

        try:
            montant = float(self.champ_montant.text)
        except ValueError:
            self.message.afficher("Saisis un montant valide.", False)
            return None

        if montant <= 0:
            self.message.afficher("Le montant doit être supérieur à zéro.", False)
            return None

        return {
            "titre": titre,
            "montant": montant,
            "categorie": categorie,
            "date": date_depense,
            "description": self.champ_description.text.strip() or None,
        }


# ==============================
# PAGE DE BASE
# ==============================

class EcranBase(Screen):
    """
    Structure commune : zone défilante (contenu) + zone fixe en bas (pied)
    pour les boutons de navigation. Les marges s'adaptent à la largeur de
    la fenêtre pour garder un contenu lisible sur grand écran.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        racine = BoxLayout(orientation="vertical")

        self.defilement = ScrollView(
            do_scroll_x=False,
            bar_width=dp(4),
            bar_color=ROSE_FONCE
        )

        self.contenu = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10)
        )
        self.contenu.bind(minimum_height=self.contenu.setter("height"))
        self.defilement.add_widget(self.contenu)

        self.pied = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8)
        )
        self.pied.bind(minimum_height=self.pied.setter("height"))

        racine.add_widget(self.defilement)
        racine.add_widget(self.pied)
        self.add_widget(racine)

        self.bind(width=self._maj_marges)
        self._maj_marges()

    def _maj_marges(self, *args):
        marge = max(dp(18), (self.width - dp(620)) / 2)
        self.contenu.padding = [marge, dp(12), marge, dp(8)]
        self.pied.padding = [marge, dp(4), marge, dp(10)]

    def aller(self, nom_page):
        self.manager.current = nom_page

    def titre_page(self, texte):
        """Ajoute un titre centré en haut du contenu."""
        self.contenu.add_widget(
            Texte(
                text=texte,
                font_size=sp(22),
                bold=True,
                color=ROSE_FONCE,
                halign="center"
            )
        )


# ==============================
# PAGE ACCUEIL
# ==============================

class EcranAccueil(EcranBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # En-tête : titre + date du jour
        entete = Carte(couleur=ROSE, rayon=FORME_A, padding=dp(10), spacing=dp(2))
        entete.add_widget(
            Texte(
                text="MES DÉPENSES",
                font_size=sp(26),
                bold=True,
                color=ROSE_FONCE,
                halign="center"
            )
        )
        self.label_date = Texte(
            font_size=sp(13),
            color=ROSE_FONCE,
            halign="center"
        )
        entete.add_widget(self.label_date)
        self.contenu.add_widget(entete)

        # Carte principale : solde restant + barre de progression
        solde = Carte(couleur=VERT, rayon=FORME_B, padding=[dp(16), dp(12)])
        solde.add_widget(
            Texte(
                text="Solde restant",
                font_size=sp(14),
                color=TEXTE_DOUX,
                halign="center"
            )
        )
        self.valeur_solde = Texte(
            text="—",
            font_size=sp(30),
            bold=True,
            halign="center"
        )
        solde.add_widget(self.valeur_solde)
        self.barre = BarreProgression()
        solde.add_widget(self.barre)
        self.label_pourcentage = Texte(
            font_size=sp(13),
            color=TEXTE_DOUX,
            halign="center"
        )
        solde.add_widget(self.label_pourcentage)
        self.contenu.add_widget(solde)

        # Budget initial et total des dépenses côte à côte
        stats = ligne_horizontale(spacing=dp(10))
        self.valeur_budget = self._ajouter_carte_stat(
            stats, "Budget initial", JAUNE
        )
        self.valeur_depenses = self._ajouter_carte_stat(
            stats, "Total des dépenses", ROSE
        )
        self.contenu.add_widget(stats)

        self.message = Message(halign="center")
        self.contenu.add_widget(self.message)

        # Navigation : action principale puis deux boutons côte à côte
        bouton_ajouter = BoutonPastel(
            text="Ajouter une dépense",
            couleur=VERT,
            rayon=23
        )
        bouton_ajouter.bind(on_press=lambda instance: self.aller("ajout"))
        self.contenu.add_widget(bouton_ajouter)

        navigation = ligne_horizontale(spacing=dp(10))
        bouton_budget = BoutonPastel(
            text="Mon budget",
            couleur=ROSE,
            rayon=23,
            style="contour"
        )
        bouton_historique = BoutonPastel(
            text="Historique",
            couleur=JAUNE,
            rayon=4,
            style="contour"
        )
        bouton_budget.bind(on_press=lambda instance: self.aller("budget"))
        bouton_historique.bind(on_press=lambda instance: self.aller("historique"))
        navigation.add_widget(bouton_budget)
        navigation.add_widget(bouton_historique)
        self.contenu.add_widget(navigation)

    def _ajouter_carte_stat(self, ligne, titre, couleur):
        """Ajoute une petite carte (titre + valeur) à la ligne et retourne le label de la valeur."""
        carte = Carte(
            couleur=BLANC,
            rayon=12,
            contour=assombrir(couleur, 0.85),
            accent=couleur,
            padding=[dp(26), dp(10), dp(12), dp(10)]
        )
        carte.add_widget(Texte(text=titre, font_size=sp(13), color=TEXTE_DOUX))
        valeur = Texte(text="—", font_size=sp(17), bold=True)
        carte.add_widget(valeur)
        ligne.add_widget(carte)
        return valeur

    def on_pre_enter(self, *args):
        self.label_date.text = date_du_jour_texte()
        self.actualiser_stats()

    def actualiser_stats(self):
        """Récupère les statistiques du budget et met à jour le tableau de bord."""
        try:
            stats = api_stats()
            budget = float(stats["budget_initial"])
            depenses = float(stats["total_depenses"])
            solde = float(stats["solde_restant"])
        except ErreurAPI as erreur:
            self._afficher_indisponible(str(erreur))
            return
        except (KeyError, TypeError, ValueError):
            self._afficher_indisponible("Réponse inattendue du serveur.")
            return

        self.valeur_budget.text = formater_montant(budget)
        self.valeur_depenses.text = formater_montant(depenses)
        self.valeur_solde.text = formater_montant(solde)

        # Part du budget déjà dépensée
        part = depenses / budget if budget > 0 else 0
        self.barre.definir(part)
        self.label_pourcentage.text = f"{part * 100:.0f} % du budget utilisé"
        self.message.effacer()

    def _afficher_indisponible(self, texte):
        self.valeur_budget.text = "—"
        self.valeur_depenses.text = "—"
        self.valeur_solde.text = "Indisponible"
        self.barre.definir(0)
        self.label_pourcentage.text = ""
        self.message.afficher(texte, False)


# ==============================
# PAGE BUDGET
# ==============================

class EcranBudget(EcranBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.titre_page("MON BUDGET")

        carte = carte_formulaire()
        carte.add_widget(
            Texte(
                text="Définis ou modifie ton budget général.",
                color=TEXTE_DOUX
            )
        )

        self.champ_budget = ChampTexte(
            hint_text="Saisir ton budget en Ariary",
            input_filter="float"
        )
        carte.add_widget(self.champ_budget)

        bouton_enregistrer = BoutonPastel(
            text="Enregistrer mon budget",
            couleur=VERT,
            rayon=23
        )
        bouton_enregistrer.bind(on_press=lambda instance: self.enregistrer())
        carte.add_widget(bouton_enregistrer)

        self.message = Message()
        carte.add_widget(self.message)

        self.contenu.add_widget(carte)

        bouton_retour = BoutonPastel(
            text="Retour à l'accueil", couleur=ROSE, rayon=12, style="contour"
        )
        bouton_retour.bind(on_press=lambda instance: self.aller("accueil"))
        self.pied.add_widget(bouton_retour)

    def on_pre_enter(self, *args):
        self.champ_budget.text = ""
        self.message.effacer()

    def enregistrer(self):
        """Valide la saisie puis envoie le nouveau budget à l'API."""
        try:
            montant = float(self.champ_budget.text)
        except ValueError:
            self.message.afficher("Saisis un montant valide.", False)
            return

        if montant <= 0:
            self.message.afficher("Le budget doit être supérieur à zéro.", False)
            return

        try:
            api_enregistrer_budget(montant)
        except ErreurAPI as erreur:
            self.message.afficher(str(erreur), False)
            return

        self.champ_budget.text = ""
        self.message.afficher("Budget enregistré avec succès !", True)


# ==============================
# PAGE AJOUT D'UNE DEPENSE
# ==============================

class EcranAjout(EcranBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.titre_page("AJOUTER UNE DÉPENSE")

        carte = carte_formulaire()
        self.formulaire = FormulaireDepense(
            "Enregistrer la dépense",
            self.enregistrer
        )
        carte.add_widget(self.formulaire)
        self.contenu.add_widget(carte)

        bouton_retour = BoutonPastel(
            text="Retour à l'accueil", couleur=ROSE, rayon=12, style="contour"
        )
        bouton_retour.bind(on_press=lambda instance: self.aller("accueil"))
        self.pied.add_widget(bouton_retour)

    def on_pre_enter(self, *args):
        self.formulaire.vider()

    def enregistrer(self):
        """Crée une nouvelle dépense datée d'aujourd'hui."""
        donnees = self.formulaire.lire_donnees(date.today().isoformat())
        if donnees is None:
            return

        try:
            api_creer_depense(donnees)
        except ErreurAPI as erreur:
            self.formulaire.message.afficher(str(erreur), False)
            return

        # On vide les champs puis on affiche la confirmation
        self.formulaire.vider()
        self.formulaire.message.afficher("Dépense enregistrée avec succès !", True)


# ==============================
# PAGE MODIFICATION D'UNE DEPENSE
# ==============================

class EcranModification(EcranBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.depense = None  # dépense en cours de modification

        self.titre_page("MODIFIER UNE DÉPENSE")

        carte = carte_formulaire()
        self.formulaire = FormulaireDepense(
            "Enregistrer les modifications",
            self.enregistrer
        )
        carte.add_widget(self.formulaire)
        self.contenu.add_widget(carte)

        bouton_annuler = BoutonPastel(
            text="Annuler", couleur=ROSE, rayon=12, style="contour"
        )
        bouton_annuler.bind(on_press=lambda instance: self.aller("historique"))
        self.pied.add_widget(bouton_annuler)

    def charger(self, depense):
        """Prépare le formulaire avec la dépense choisie dans l'historique."""
        self.depense = depense
        self.formulaire.remplir(depense)

    def enregistrer(self):
        """Envoie les modifications (la date d'origine est conservée)."""
        if self.depense is None:
            return

        donnees = self.formulaire.lire_donnees(self.depense.get("date", ""))
        if donnees is None:
            return

        try:
            api_modifier_depense(self.depense["id"], donnees)
        except ErreurAPI as erreur:
            self.formulaire.message.afficher(str(erreur), False)
            return

        historique = self.manager.get_screen("historique")
        historique.message_en_attente = ("Dépense modifiée avec succès !", True)
        self.aller("historique")


# ==============================
# PAGE HISTORIQUE
# ==============================

class EcranHistorique(EcranBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.message_en_attente = None  # (texte, succes) à afficher après actualisation

        self.titre_page("HISTORIQUE DES DÉPENSES")

        self.label_compteur = Texte(
            font_size=sp(18),
            bold=True,
            halign="center"
        )
        self.message = Message(halign="center")

        self.zone_liste = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8)
        )
        self.zone_liste.bind(minimum_height=self.zone_liste.setter("height"))

        self.contenu.add_widget(self.label_compteur)
        self.contenu.add_widget(self.message)
        self.contenu.add_widget(self.zone_liste)

        # Boutons fixes en bas de page
        bouton_actualiser = BoutonPastel(text="Actualiser", couleur=VERT, rayon=23)
        bouton_actualiser.bind(on_press=lambda instance: self.actualiser())

        bouton_retour = BoutonPastel(
            text="Retour à l'accueil", couleur=ROSE, rayon=12, style="contour"
        )
        bouton_retour.bind(on_press=lambda instance: self.aller("accueil"))

        self.pied.add_widget(bouton_actualiser)
        self.pied.add_widget(bouton_retour)

    def on_pre_enter(self, *args):
        reussi = self.actualiser()

        if reussi and self.message_en_attente:
            texte, succes = self.message_en_attente
            self.message.afficher(texte, succes)
        self.message_en_attente = None

    def on_leave(self, *args):
        self.message.effacer()

    def actualiser(self):
        """Recharge la liste depuis l'API. Retourne True si tout s'est bien passé."""
        self.zone_liste.clear_widgets()
        self.message.effacer()

        try:
            depenses = api_lister_depenses()
            if not isinstance(depenses, list):
                raise ErreurAPI("Réponse inattendue du serveur.")

            # De la plus récente à la plus ancienne
            depenses.sort(
                key=lambda d: (d.get("date") or "", d.get("id") or 0),
                reverse=True
            )
        except ErreurAPI as erreur:
            self.label_compteur.text = ""
            self.message.afficher(str(erreur), False)
            return False

        if not depenses:
            self.label_compteur.text = "Aucune dépense enregistrée."
            return True

        self.label_compteur.text = f"TOUTES MES DÉPENSES ({len(depenses)})"

        for index, depense in enumerate(depenses):
            self.zone_liste.add_widget(self._creer_carte(depense, index))

        return True

    def _creer_carte(self, depense, index):
        """Construit la carte d'une dépense avec ses boutons Modifier / Supprimer."""
        couleur_accent = (ROSE, JAUNE, VERT)[index % 3]
        carte = Carte(
            couleur=BLANC,
            rayon=12,
            contour=assombrir(couleur_accent, 0.85),
            accent=couleur_accent,
            padding=[dp(26), dp(10), dp(12), dp(10)]
        )

        # Titre + montant
        haut = ligne_horizontale(spacing=dp(8))
        haut.add_widget(
            Texte(
                text=str(depense.get("titre") or ""),
                bold=True,
                size_hint_x=0.6
            )
        )
        haut.add_widget(
            Texte(
                text=formater_montant(depense.get("montant") or 0),
                bold=True,
                color=ROSE_FONCE,
                halign="right",
                size_hint_x=0.4
            )
        )
        carte.add_widget(haut)

        # Numéro, catégorie, date et description (si elle existe)
        details = (
            f"N° {depense.get('id', '?')}  ·  "
            f"{depense.get('categorie') or ''}  ·  "
            f"{depense.get('date') or ''}"
        )
        if depense.get("description"):
            details += f"\n{depense['description']}"

        carte.add_widget(
            Texte(text=details, font_size=sp(13), color=TEXTE_DOUX)
        )

        # Boutons d'action
        actions = ligne_horizontale(spacing=dp(10))

        bouton_modifier = BoutonPastel(
            text="Modifier",
            couleur=JAUNE,
            rayon=10,
            style="contour",
            height=dp(36)
        )
        bouton_supprimer = BoutonPastel(
            text="Supprimer",
            couleur=ROSE,
            rayon=10,
            style="contour",
            height=dp(36)
        )

        bouton_modifier.bind(
            on_press=lambda instance, d=depense: self.modifier(d)
        )
        bouton_supprimer.bind(
            on_press=lambda instance, d=depense: self.confirmer_suppression(d)
        )

        actions.add_widget(bouton_modifier)
        actions.add_widget(bouton_supprimer)
        carte.add_widget(actions)

        return carte

    def modifier(self, depense):
        """Ouvre la page de modification avec la dépense choisie."""
        self.manager.get_screen("modification").charger(depense)
        self.aller("modification")

    def confirmer_suppression(self, depense):
        """Demande une confirmation avant de supprimer la dépense."""
        fenetre = ModalView(
            size_hint=(None, None),
            size=(min(dp(420), Window.width * 0.9), dp(230)),
            background="",
            background_color=(0, 0, 0, 0),
            overlay_color=(0, 0, 0, 0.35)
        )

        carte = Carte(
            couleur=BLANC,
            rayon=16,
            contour=CONTOUR,
            size_hint_y=1,
            padding=dp(20),
            spacing=dp(10)
        )
        carte.add_widget(
            Texte(
                text="Supprimer cette dépense ?",
                font_size=sp(19),
                bold=True,
                color=ROSE_FONCE
            )
        )
        carte.add_widget(Texte(text=f"« {depense.get('titre') or ''} »"))
        carte.add_widget(Widget())  # espace flexible

        boutons = ligne_horizontale(spacing=dp(10))
        bouton_non = BoutonPastel(
            text="Annuler", couleur=JAUNE, rayon=12, style="contour"
        )
        bouton_oui = BoutonPastel(text="Oui, supprimer", couleur=ROSE, rayon=12)
        boutons.add_widget(bouton_non)
        boutons.add_widget(bouton_oui)
        carte.add_widget(boutons)

        fenetre.add_widget(carte)

        def supprimer(instance):
            fenetre.dismiss()

            try:
                api_supprimer_depense(depense["id"])
                resultat = ("Dépense supprimée avec succès.", True)
            except ErreurAPI as erreur:
                resultat = (str(erreur), False)

            # Si la liste n'a pas pu être rechargée, son message d'erreur reste affiché
            if self.actualiser():
                self.message.afficher(*resultat)

        bouton_oui.bind(on_press=supprimer)
        bouton_non.bind(on_press=lambda instance: fenetre.dismiss())

        fenetre.open()


# ==============================
# APPLICATION
# ==============================

class MesDepensesApp(App):

    title = "Mes dépenses"

    def build(self):
        Window.clearcolor = FOND

        # Gestionnaire des pages
        gestionnaire = ScreenManager(transition=FadeTransition(duration=0.15))

        gestionnaire.add_widget(EcranAccueil(name="accueil"))
        gestionnaire.add_widget(EcranBudget(name="budget"))
        gestionnaire.add_widget(EcranAjout(name="ajout"))
        gestionnaire.add_widget(EcranHistorique(name="historique"))
        gestionnaire.add_widget(EcranModification(name="modification"))

        return gestionnaire


if __name__ == "__main__":
    MesDepensesApp().run()
