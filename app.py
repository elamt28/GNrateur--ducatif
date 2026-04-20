import streamlit as st
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
                    st.download_button("📥 Retélécharger en WORD", generer_docx(item.get('sujet'), item.get('contenu')), f"Ancien_Cours_{item.get('sujet')}.docx", key=item.get('timestamp'))
