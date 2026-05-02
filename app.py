import streamlit as st
import google.generativeai as genai
import datetime
from io import BytesIO

# --- CONFIGURATION DE LA PAGE (OBLIGATOIREMENT EN PREMIER) ---
st.set_page_config(page_title="EduForge Pro V33", layout="wide")

# --- VÉRIFICATION DES MODULES ---
try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# --- CONFIGURATION SÉCURISÉE ---
APP_ID = globals().get('__app_id', 'eduforge-pro-master-cfa')

# --- MÉMOIRE DE SESSION ---
if 'cours_memoire' not in st.session_state:
    st.session_state.cours_memoire = None
if 'sujet_memoire' not in st.session_state:
    st.session_state.sujet_memoire = None

# --- MOTEUR DE GÉNÉRATION V33 (TRANSFERT DE COMPÉTENCE) ---
def forger_cours_v33(formation, sujet, lieu, moteur, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(moteur)
    
    prompt = f"""
    Tu es l'ingénieur pédagogique expert du CFA Interpro de Chartres. 
    Module de 60 minutes. Formation : {formation}. Sujet : {sujet}. 
    Localisation : {lieu} (Chartres/Champhol).
    
    EXIGENCES V33 (TRANSFERT DE COMPÉTENCE) :
    1. Ton ludique, humour technique et jeux de mots.
    2. SECTION OBLIGATOIRE : "Et si la situation changeait ?". 
       Propose une variante du scénario initial avec une contrainte supplémentaire (ex: panne intermittente, urgence client, rupture de stock).
       Demande à l'apprenti d'expliquer comment sa procédure technique doit évoluer.
    3. STRUCTURE : 
       - # 🎓 TITRE DU MODULE
       - ## 🎯 RÉFÉRENTIEL MÉTIER
       - ## 🎬 SCÉNARIO PRINCIPAL (Humour local)
       - ## 📖 CŒUR TECHNIQUE CERTIFIÉ
       - ## 🔄 ET SI LA SITUATION CHANGEAIT ? (Transfert)
       - ## 📝 ÉVALUATION SOMMATIVE (/20)
       - ## 👨‍🏫 CORRECTION & ANALYSE DU TRANSFERT
    4. Ne cite JAMAIS 'Manu'.
    """
    return model.generate_content(prompt).text

# --- EXPORT WORD V33 ---
def generer_docx_v33(titre, contenu):
    if not HAS_DOCX: return None
    doc = Document()
    t = doc.add_heading(titre, 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    for ligne in contenu.split('\n'):
        if ligne.startswith('# '):
            doc.add_heading(ligne.replace('# ', ''), level=1)
        elif ligne.startswith('## '):
            p = doc.add_heading(ligne.replace('## ', ''), level=2)
            if "CHANGEAIT" in ligne:
                p.runs[0].font.color.rgb = RGBColor(0, 153, 153) # Cyan pour le transfert
        else:
            doc.add_paragraph(ligne)
            
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()

# --- INTERFACE ---
st.title("⚡ EduForge Pro : Transfert V33")
st.markdown("*L'ingénierie qui prépare les apprentis aux imprévus du métier - Chartres*")

with st.sidebar:
    st.header("🔑 Configuration")
    api_key = st.text_input("Clé Gemini :", type="password")
    if api_key:
        moteur = st.selectbox("Moteur IA :", ["gemini-1.5-flash", "gemini-2.0-flash-exp"])
    
    st.divider()
    formations = ["BTS Maintenance Véhicule", "Bac Pro Maintenance Véhicule", "BP Boulanger", "BP Boucher", "CAP EPC", "BP Coiffure", "AMLHR"]
    f_sel = st.selectbox("Formation visée :", formations)
    sujet_in = st.text_input("Thème technique :")
    lieu_in = st.text_input("Lieu du scénario :", value="Chartres / Champhol")
    
    # CORRECTIF ANTI-CRASH : Clé statique pour le bouton
    if st.button("🚀 Forger le Module", key="btn_forge_v33"):
        if api_key and sujet_in:
            with st.spinner("Analyse des compétences et création du scénario miroir..."):
                try:
                    res = forger_cours_v33(f_sel, sujet_in, lieu_in, moteur, api_key)
                    st.session_state.cours_memoire = res
                    st.session_state.sujet_memoire = sujet_in
                except Exception as e: st.error(f"Erreur : {e}")

# CORRECTIF ANTI-CRASH : Ancrage du conteneur d'affichage avant la condition
result_container = st.container()

with result_container:
    # --- AFFICHAGE ---
    if st.session_state.cours_memoire:
        col_t, col_dl = st.columns([4, 1])
        with col_t:
            st.success(f"✅ Module '{st.session_state.sujet_memoire}' forgé avec scénario de transfert.")
        with col_dl:
            if HAS_DOCX:
                data = generer_docx_v33(st.session_state.sujet_memoire, st.session_state.cours_memoire)
                # Clé de téléchargement sécurisée
                st.download_button("📥 WORD", data, f"Transfert_{st.session_state.sujet_memoire}.docx", key="dl_v33_master")
        
        st.divider()
        st.markdown(st.session_state.cours_memoire)
