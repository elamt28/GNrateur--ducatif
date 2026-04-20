importimport streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import InvalidArgument, ResourceExhausted
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import qrcode
from io import BytesIO
import json
import os
import datetime

# Imports pour la sauvegarde sécurisée
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    pass

# --- CONFIGURATION DES VARIABLES GLOBALES ---
APP_ID = globals().get('__app_id', 'gnrateur-educatif-cfa')
FIREBASE_CONFIG = globals().get('__firebase_config')

# --- INITIALISATION DU STOCKAGE (SÉCURISÉ) ---
def init_storage():
    if not FIREBASE_CONFIG:
        return None
    try:
        if not firebase_admin._apps:
            conf = json.loads(FIREBASE_CONFIG)
            cred = credentials.Certificate(conf)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception:
        return None

db = init_storage()

# --- FONCTIONS DE SAUVEGARDE ET RÉCUPÉRATION ---
def sauvegarder_dans_historique(formation, sujet, contenu):
    if not db:
        return
    try:
        # Chemin strict selon la règle 1 : /artifacts/{appId}/public/data/{collection}
        # On utilise 'public' car on veut pouvoir consulter ses cours partout
        doc_ref = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('historique').document()
        doc_ref.set({
            'formation': formation,
            'sujet': sujet,
            'contenu': contenu,
            'date': datetime.datetime.now(),
            'timestamp': datetime.datetime.now().timestamp()
        })
    except Exception as e:
        print(f"Erreur sauvegarde : {e}")

def recuperer_historique():
    if not db:
        return []
    try:
        # Règle 2 : Requête simple sans orderBy complexe (tri manuel après)
        docs = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('historique').stream()
        results = [doc.to_dict() for doc in docs]
        # Tri en mémoire Python
        results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return results
    except Exception:
        return []

# --- FONCTIONS EXPORT ET UTILITAIRES ---
def generer_docx(titre, contenu):
    doc = Document()
    header = doc.add_heading(titre, 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lignes = contenu.split('\n')
    for ligne in lignes:
        if ligne.startswith('# '): doc.add_heading(ligne.replace('# ', ''), level=1)
        elif ligne.startswith('## '): doc.add_heading(ligne.replace('## ', ''), level=2)
        elif ligne.startswith('### '): doc.add_heading(ligne.replace('### ', ''), level=3)
        elif ligne.startswith('**'):
            p = doc.add_paragraph()
            p.add_run(ligne.replace('**', '')).bold = True
        else: doc.add_paragraph(ligne)
    output = BytesIO()
    doc.save(output)
    return output.getvalue()

def generer_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

def suggerer_sujets(formation, api_key):
    genai.configure(api_key=api_key)
    model_name = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods][0]
    model = genai.GenerativeModel(model_name)
    prompt = f"Expert pédagogique CFA Chartres : Propose 5 sujets techniques pour {formation}. Liste à puces."
    reponse = model.generate_content(prompt)
    return reponse.text

def generer_cours_complet(formation, sujet, localisation, moteur_choisi):
    model = genai.GenerativeModel(moteur_choisi)
    prompt = f"""
    Expert ingénieur pédagogique. Rédige un cours complet pour {formation} sur {sujet}.
    Lieu : {localisation}. Ton ludique, humour, sans nommer Manu.
    STRUCTURE : 
    1. Référentiel codes/savoirs.
    2. Scénario local Chartres.
    3. Notions clés.
    4. Activités (QCM, Vrai/Faux, Association).
    5. Évaluation notée sur 20 avec barème.
    6. Espace Formateur (Correction détaillée) à la fin.
    """
    reponse = model.generate_content(prompt)
    return reponse.text

@st.cache_data(show_spinner=False)
def obtenir_modeles_disponibles(api_key):
    genai.configure(api_key=api_key)
    try:
        return [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except: return []

# --- INTERFACE UTILISATEUR ---
st.title("📝 GNrateur contenu éducatif")
st.markdown("L'outil d'ingénierie pédagogique infaillible du CFA Interpro de Chartres.")

tab_gen, tab_hist = st.tabs(["🚀 Nouveau Cours", "📚 Historique & Sauvegarde"])

with st.sidebar:
    st.header("🔑 Accès")
    api_key = st.text_input("Clé API Google Gemini :", type="password")
    st.divider()
    if api_key:
        liste_moteurs = obtenir_modeles_disponibles(api_key)
        moteur_ia = st.selectbox("Moteur IA :", liste_moteurs) if liste_moteurs else None
    else: moteur_ia = None

with tab_gen:
    st.header("⚙️ Paramètres de génération")
    options_formation = ["Bac Pro Maintenance Véhicule (2de)", "Bac Pro Maintenance Véhicule (1re)", "Bac Pro Maintenance Véhicule (Term)", "BTS Maintenance Véhicule", "Carrossier/Peintre", "BP Boulanger", "BM Boulanger", "BP Boucher", "CAP EPC", "BP Coiffure", "AMLHR", "➕ Autre"]
    formation_sel = st.selectbox("Formation :", options_formation)
    formation = st.text_input("Précisez la formation :") if formation_sel == "➕ Autre" else formation_sel
    
    if st.button("💡 Suggérer des idées de sujets"):
        if api_key and formation:
            st.info(suggerer_sujets(formation, api_key))
            
    sujet = st.text_input("Sujet du cours :", placeholder="Ex: Injection directe, Levains...")
    localisation = st.text_input("Localisation :", value="Chartres / Champhol")
    lancer = st.button("🚀 Forger le Document", use_container_width=True)

    if lancer and sujet and moteur_ia:
        genai.configure(api_key=api_key)
        with st.spinner("Forgeage en cours..."):
            try:
                document_cours = generer_cours_complet(formation, sujet, localisation, moteur_ia)
                # SAUVEGARDE AUTOMATIQUE
                sauvegarder_dans_historique(formation, sujet, document_cours)
                
                st.success("✅ Document généré et sauvegardé !")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("📥 Télécharger WORD", generer_docx(sujet, document_cours), f"{sujet}.docx")
                with col2:
                    st.image(generer_qr_code("https://www.cfa-interpro-28.fr/"), width=100)
                st.markdown(document_cours)
            except ResourceExhausted: st.error("Quota dépassé. Attendez 1 min.")
            except Exception as e: st.error(f"Erreur : {e}")

with tab_hist:
    st.header("📂 Vos archives pédagogiques")
    if not db:
        st.warning("⚠️ Le système de sauvegarde n'est pas encore configuré sur ce serveur.")
    else:
        historique = recuperer_historique()
        if not historique:
            st.info("Aucun cours n'a encore été sauvegardé. Commencez par en forger un !")
        else:
            for item in historique:
                with st.expander(f"📅 {item.get('date').strftime('%d/%m/%Y %H:%M')} - {item.get('formation')} : {item.get('sujet')}"):
                    st.markdown(item.get('contenu'))
                    st.download_button("📥 Retélécharger en WORD", generer_docx(item.get('sujet'), item.get('contenu')), f"Ancien_Cours_{item.get('sujet')}.docx", key=item.get('timestamp')) streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import InvalidArgument, ResourceExhausted

# --- CONFIGURATION EXPERTE ---
st.set_page_config(page_title="GNrateur contenu éducatif", layout="wide", page_icon="📝")

# --- MOTEUR DE GÉNÉRATION ROBUSTE (TEXTE STRUCTURÉ) ---
def generer_cours_complet(formation, sujet, localisation, moteur_choisi):
    """
    Génère un cours complet en Markdown en utilisant le modèle sélectionné.
    """
    model = genai.GenerativeModel(moteur_choisi)
    
    prompt = f"""
    Agis en tant que meilleur expert ingénieur pédagogique. Tu dois rédiger un document de cours "clef en main" pour des apprentis.
    
    PARAMÈTRES :
    - Formation visée : {formation}
    - Sujet du cours : {sujet}
    - Localisation du scénario : {localisation}
    
    CONSIGNES STRICTES D'EXCELLENCE :
    1. Le ton doit être ludique, avec une pointe d'humour et des jeux de mots.
    2. Ne cite JAMAIS le prénom "Manu" dans le cours.
    3. La correction de TOUTES les activités doit IMPÉRATIVEMENT se trouver dans une section isolée, tout à la fin du document.
    4. Sois exigeant sur le vocabulaire technique adapté au niveau de la formation.
    
    STRUCTURE OBLIGATOIRE DU DOCUMENT :
    
    # 🎓 Cours : {sujet}
    **Formation :** {formation} | **Lieu du scénario :** {localisation}
    
    ## 🎯 Référentiel visé (Compétences et Savoirs)
    [Détaille ici de manière exacte et certifiée les codes (ex: C1.2, S3) et les descriptions des compétences du référentiel officiel concernées par cette leçon.]
    
    ## 🎬 Scénario Pédagogique
    [Une accroche ludique ancrée géographiquement.]
    
    ## 📖 Notions Clés & Mission
    [Le cœur du cours, clair, structuré, prêt à être lu par les apprentis.]
    
    ## 🧠 Activités Pédagogiques
    
    ### A. QCM
    [3 questions pointues avec choix multiples A, B, C]
    
    ### B. Vrai ou Faux
    [3 affirmations techniques à valider]
    
    ### C. Jeu d'associations
    [Mélange 4 mots techniques de la leçon avec 4 définitions. L'apprenti doit les relier.]
    
    ---
    
    ## 👨‍🏫 ESPACE FORMATEUR (CORRECTIONS)
    [Cette section est pour le formateur. Donne les corrections exactes et auto-critiquées du QCM, du Vrai/Faux, et du jeu d'associations. Justifie les réponses.]
    """
    
    reponse = model.generate_content(prompt)
    return reponse.text

# --- FONCTION DE RÉCUPÉRATION DES MODÈLES (ANTI-404) ---
@st.cache_data(show_spinner=False)
def obtenir_modeles_disponibles(api_key):
    """
    Interroge l'API Google pour lister uniquement les modèles de génération de texte
    réellement disponibles pour la clé API fournie.
    """
    genai.configure(api_key=api_key)
    modeles_valides = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # On nettoie le nom (ex: "models/gemini-pro" devient "gemini-pro")
                nom_propre = m.name.replace("models/", "")
                modeles_valides.append(nom_propre)
    except Exception as e:
        # En cas d'erreur (ex: clé invalide au démarrage), on renvoie une liste vide
        return []
    
    # On trie pour mettre les modèles 'flash' (souvent plus rapides) en premier
    modeles_valides.sort(key=lambda x: "flash" not in x)
    return modeles_valides

# --- INTERFACE UTILISATEUR ---
st.title("📝 GNrateur contenu éducatif")
st.markdown("L'outil d'ingénierie pédagogique infaillible du CFA. Générez des documents structurés, conformes et prêts à imprimer.")

with st.sidebar:
    st.header("🔑 Accès Sécurisé")
    st.markdown("[Obtenir une clé API gratuite ici](https://aistudio.google.com/app/apikey)")
    api_key = st.text_input("Clé API Google Gemini :", type="password", help="Insérez votre clé API valide ici. Elle n'est pas sauvegardée et reste locale.")
    
    st.divider()

    st.header("⚙️ Paramètres du Moteur")
    
    # --- GESTION DYNAMIQUE DU SÉLECTEUR DE MOTEUR ---
    if api_key:
        liste_moteurs = obtenir_modeles_disponibles(api_key)
        if liste_moteurs:
             moteur_ia = st.selectbox(
                "Sélectionnez le moteur IA (Changez si erreur 429) :",
                liste_moteurs
            )
             st.caption("Astuce : Si un moteur est saturé, essayez-en un autre dans la liste.")
        else:
             st.error("Impossible de récupérer la liste des modèles. Vérifiez votre clé API.")
             moteur_ia = None
    else:
        st.info("Veuillez saisir votre clé API pour afficher les moteurs disponibles.")
        moteur_ia = None

    st.divider()
    
    st.header("⚙️ Paramètres de la session")
    
    # Gestion de la formation avec option "Autre"
    options_formation = [
        "Bac Pro Maintenance Véhicule (2de)", "Bac Pro Maintenance Véhicule (1re)", "Bac Pro Maintenance Véhicule (Term)",
        "BTS Maintenance Véhicule", "Carrossier/Peintre",
        "BP Boulanger", "BM Boulanger", "BP Boucher", 
        "CAP Équipier Polyvalent du Commerce (EPC)", 
        "BP Coiffure", "AMLHR (Hôtellerie-Restauration)",
        "➕ Autre (à préciser)"
    ]
    
    formation_selectionnee = st.selectbox("Formation concernée :", options_formation)
    
    if formation_selectionnee == "➕ Autre (à préciser)":
        formation = st.text_input("Précisez la formation :", placeholder="Ex: CAP Pâtissier...")
    else:
        formation = formation_selectionnee

    sujet = st.text_input("Sujet du cours :", placeholder="Ex: L'allumage électronique, Le pétrissage...")
    localisation = st.text_input("Localisation :", value="Chartres / Champhol")
    lancer = st.button("🚀 Générer le Document", use_container_width=True)

# Validation de la clé API avant lancement
if lancer:
    if not api_key:
        st.warning("👈 Veuillez entrer votre clé API Gemini dans le menu de gauche pour démarrer le moteur.")
        st.stop()
    elif not moteur_ia:
        st.warning("Aucun moteur IA n'est sélectionné. Vérifiez votre clé API.")
        st.stop()
    elif not formation:
         st.warning("Veuillez indiquer une formation concernée.")
         st.stop()
    elif not sujet:
        st.warning("Veuillez indiquer un sujet de cours.")
        st.stop()
    else:
        # Configuration de la clé saisie par l'utilisateur
        genai.configure(api_key=api_key)
        
        with st.spinner(f"Rédaction du document avec le moteur {moteur_ia} (Processus blindé en cours)..."):
            try:
                # 1. Génération du contenu brut
                document_cours = generer_cours_complet(formation, sujet, localisation, moteur_ia)
                
                st.success("✅ Document généré avec succès ! Aucun crash détecté.")
                
                # 2. Bouton de téléchargement robuste
                st.download_button(
                    label="📥 Télécharger le Document (Format Texte)", 
                    data=document_cours, 
                    file_name=f"Cours_{formation.replace(' ', '_')}_{sujet.replace(' ', '_')}.txt", 
                    mime="text/plain"
                )
                
                st.info("💡 Astuce : Vous pouvez cliquer sur 'Télécharger', ou simplement copier/coller le texte ci-dessous directement dans Word. Word conservera la mise en forme (Titres, gras, puces).")
                st.divider()
                
                # 3. Affichage pleine page
                st.markdown(document_cours)
                    
            except InvalidArgument:
                st.error("🚨 La clé API saisie n'est pas valide. Veuillez vérifier que vous avez copié l'intégralité de la clé depuis Google AI Studio sans espace supplémentaire.")
            except ResourceExhausted as e:
                st.error(f"🚨 Le moteur {moteur_ia} est actuellement saturé (Erreur 429 - Quota dépassé).")
                st.warning("🛠️ Solution : Essayez de sélectionner un autre 'Moteur IA' dans la barre latérale, ou vérifiez vos quotas journaliers sur Google AI Studio.")
            except Exception as e:
                # Traitement des autres erreurs imprévues (réseau, surcharge serveur...)
                error_message = str(e)
                if "API_KEY_INVALID" in error_message:
                    st.error("🚨 Clé API refusée par le serveur Google. Vérifiez votre clé.")
                elif "429" in error_message or "quota" in error_message.lower():
                     # Fallback si l'exception n'est pas captée comme ResourceExhausted
                    st.error(f"🚨 Le moteur {moteur_ia} est actuellement saturé (Erreur 429). Essayez un autre modèle dans le menu de gauche.")
                else:
                    st.error("🚨 Une erreur de connexion au serveur est survenue. Veuillez réessayer dans quelques instants.")
                    st.code(error_message)
