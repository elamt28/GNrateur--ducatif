import streamlit as st
import google.generativeai as genai
from io import BytesIO

# --- 1. CONFIGURATION DE LA PAGE (PREMIÈRE LIGNE OBLIGATOIRE) ---
st.set_page_config(page_title="EduForge Pro V37", layout="wide", page_icon="⚡")

# --- 2. VÉRIFICATION DU MODULE WORD ---
try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# --- 3. MÉMOIRE DE SESSION (SÉCURISÉE) ---
for key in ['cours_memoire', 'sujet_memoire']:
    if key not in st.session_state:
        st.session_state[key] = None

# --- 4. MOTEUR DE GÉNÉRATION V37 (PÉDAGOGIE EXPERTE CFA CHARTRES) ---
def forger_cours_v37(formation, sujet, lieu, moteur, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(moteur)
    
    prompt = f"""
    Agis en expert pédagogique du CFA Interpro de Chartres. 
    Module FOAD de 60 minutes minimum. Formation : {formation}. Sujet : {sujet}. 
    Localisation : {lieu} (Chartres/Champhol).
    
    RÈGLES ABSOLUES ET CERTIFIÉES :
    1. NE SALUE PAS au début du cours (Pas de "Bonjour", "Bienvenue", etc.). Rentre dans le vif du sujet.
    2. Ne cite JAMAIS le prénom 'Manu'.
    3. Ton ludique, humour technique et jeux de mots.
    4. Exactitude certifiée : auto-critique la logique de tes arguments, n'invente rien, pas de réponses superficielles.
    5. NE PROPOSE PAS de diapositives ou PowerPoint.
    6. Respecte scrupuleusement la structure du plan avec missions, exercices et synthèses.
    
    STRUCTURE EXHAUSTIVE : 
    - # 🎓 TITRE DU MODULE
    - ## 🎯 RÉFÉRENTIEL MÉTIER
    - ## 🎬 SCÉNARIO PRINCIPAL (Humour local)
    - ## 📖 CŒUR TECHNIQUE CERTIFIÉ (Logique argumentée)
    - ## 🔄 ET SI LA SITUATION CHANGEAIT ? (Transfert de compétence)
    - ## 📝 ÉVALUATION SOMMATIVE (/20)
    - ## 👨‍🏫 CORRECTION & AUTO-CRITIQUE (Justifie tes réponses pour prouver leur exactitude)
    """
    return model.generate_content(prompt).text

# --- 5. EXPORT WORD ---
def generer_docx(titre, contenu):
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
                p.runs[0].font.color.rgb = RGBColor(0, 153, 153) # Cyan
        else:
            doc.add_paragraph(ligne)
            
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()

# --- 6. INTERFACE UTILISATEUR ---
st.title("⚡ EduForge Pro : V37 (Architecture Native)")
st.markdown("*L'ingénierie certifiée du CFA Interpro de Chartres*")

with st.sidebar:
    st.header("🔑 Configuration")
    api_key = st.text_input("Clé Gemini :", type="password")
    moteur = st.selectbox("Moteur IA :", ["gemini-1.5-flash", "gemini-2.5-flash"])
    
    st.divider()
    
    with st.form("formulaire_forge"):
        st.header("🛠️ Paramètres du cours")
        formations = [
            "BTS Maintenance Véhicule", 
            "Bac Pro Maintenance Véhicule (2de, 1re, Term)", 
            "Carrossier/Peintre",
            "BM Boulanger",
            "BP Boulanger", 
            "BP Boucher", 
            "CAP EPC", 
            "BP Coiffure", 
            "AMLHR"
        ]
        f_sel = st.selectbox("Formation visée :", formations)
        sujet_in = st.text_input("Thème technique :")
        lieu_in = st.text_input("Lieu du scénario :", value="Chartres / Champhol")
        
        bouton_lancer = st.form_submit_button("🚀 Forger le Module")

# --- 7. LOGIQUE D'EXÉCUTION ---
if bouton_lancer:
    if not api_key:
        st.error("⚠️ La Clé API est manquante.")
    elif not sujet_in:
        st.error("⚠️ Le thème technique est requis.")
    else:
        with st.spinner("Analyse des compétences et vérification d'exactitude..."):
            try:
                res = forger_cours_v37(f_sel, sujet_in, lieu_in, moteur, api_key)
                st.session_state.cours_memoire = res
                st.session_state.sujet_memoire = sujet_in
            except Exception as e:
                st.error(f"❌ Erreur de génération : {e}")

# --- 8. ZONE D'AFFICHAGE ---
if st.session_state.cours_memoire:
    st.success(f"✅ Module '{st.session_state.sujet_memoire}' forgé avec exactitude.")
    
    if HAS_DOCX:
        data = generer_docx(st.session_state.sujet_memoire, st.session_state.cours_memoire)
        st.download_button(
            label="📥 Télécharger le Document WORD", 
            data=data, 
            file_name=f"Cours_FOAD_{st.session_state.sujet_memoire}.docx", 
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        st.warning("⚠️ Module Word désactivé (Erreur d'import des dépendances).")
        
    st.divider()
    st.markdown(st.session_state.cours_memoire)
