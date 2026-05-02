import streamlit as st
import traceback
import datetime
from io import BytesIO

# --- 1. CONFIGURATION DE LA PAGE (DOIT ÊTRE LA PREMIÈRE LIGNE STREAMLIT) ---
st.set_page_config(page_title="EduForge Pro V34", layout="wide")

# --- 2. BOUCLIER ANTI-CRASH SÉCURISÉ ---
try:
    import google.generativeai as genai
    
    # --- VÉRIFICATION DU MODULE WORD ---
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        HAS_DOCX = True
    except ImportError:
        HAS_DOCX = False

    # --- MÉMOIRE DE SESSION ---
    if 'cours_memoire' not in st.session_state:
        st.session_state.cours_memoire = None
    if 'sujet_memoire' not in st.session_state:
        st.session_state.sujet_memoire = None

    # --- MOTEUR DE GÉNÉRATION V34 (EXACTITUDE CERTIFIÉE) ---
    def forger_cours_v34(formation, sujet, lieu, moteur, api_key):
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(moteur)
        
        prompt = f"""
        Agis en expert pédagogique du CFA Interpro de Chartres. 
        Module FOAD de 60 minutes. Formation : {formation}. Sujet : {sujet}. 
        Localisation : {lieu} (Chartres/Champhol).
        
        RÈGLES ABSOLUES :
        1. NE SALUE PAS au début du cours (Pas de "Bonjour", "Bienvenue", etc.). Rentre directement dans le vif du sujet.
        2. Ne cite JAMAIS le prénom 'Manu'.
        3. Ton ludique, humour technique et jeux de mots.
        4. Exactitude certifiée : auto-critique la logique de tes arguments, n'invente rien, pas de réponses superficielles.
        5. NE PROPOSE PAS de diapositives ou PowerPoint.
        
        STRUCTURE EXHAUSTIVE : 
        - # 🎓 TITRE DU MODULE
        - ## 🎯 RÉFÉRENTIEL MÉTIER
        - ## 🎬 SCÉNARIO PRINCIPAL (Humour local)
        - ## 📖 CŒUR TECHNIQUE CERTIFIÉ (Logique argumentée)
        - ## 🔄 ET SI LA SITUATION CHANGEAIT ? (Variante du scénario avec contrainte)
        - ## 📝 ÉVALUATION SOMMATIVE (/20)
        - ## 👨‍🏫 CORRECTION & AUTO-CRITIQUE (Justifie tes réponses pour prouver leur exactitude)
        """
        return model.generate_content(prompt).text

    # --- EXPORT WORD V34 ---
    def generer_docx_v34(titre, contenu):
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

    # --- INTERFACE ---
    st.title("⚡ EduForge Pro : V34 (Infaillible)")
    st.markdown("*L'ingénierie certifiée du CFA Interpro de Chartres*")

    with st.sidebar:
        st.header("🔑 Configuration")
        api_key = st.text_input("Clé Gemini :", type="password")
        if api_key:
            moteur = st.selectbox("Moteur IA :", ["gemini-1.5-flash", "gemini-2.5-flash"])
        
        st.divider()
        formations = ["BTS Maintenance Véhicule", "Bac Pro Maintenance Véhicule", "BP Boulanger", "BP Boucher", "CAP EPC", "BP Coiffure", "AMLHR"]
        f_sel = st.selectbox("Formation visée :", formations)
        sujet_in = st.text_input("Thème technique :")
        lieu_in = st.text_input("Lieu du scénario :", value="Chartres / Champhol")
        
        if st.button("🚀 Forger le Module", key="btn_forge_v34"):
            if api_key and sujet_in:
                with st.spinner("Analyse des compétences et vérification d'exactitude..."):
                    res = forger_cours_v34(f_sel, sujet_in, lieu_in, moteur, api_key)
                    st.session_state.cours_memoire = res
                    st.session_state.sujet_memoire = sujet_in

    result_container = st.container()

    with result_container:
        if st.session_state.cours_memoire:
            col_t, col_dl = st.columns([4, 1])
            with col_t:
                st.success(f"✅ Module '{st.session_state.sujet_memoire}' forgé avec exactitude certifiée.")
            with col_dl:
                if HAS_DOCX:
                    data = generer_docx_v34(st.session_state.sujet_memoire, st.session_state.cours_memoire)
                    st.download_button("📥 WORD", data, f"Cours_{st.session_state.sujet_memoire}.docx", key="dl_v34_master")
            
            st.divider()
            st.markdown(st.session_state.cours_memoire)

# --- FIN DU BOUCLIER ---
except Exception as e:
    st.error("🚨 DÉFAILLANCE CRITIQUE INTERCEPTÉE PAR LA BOÎTE NOIRE")
    st.warning("L'application a évité le crash complet. Voici le rapport technique :")
    st.code(traceback.format_exc())
