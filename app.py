import streamlit as st

# --- 1. CONFIGURATION DE LA PAGE (OBLIGATOIREMENT EN PREMIER) ---
try:
    st.set_page_config(page_title="EduForge Pro V33.1", layout="wide")
except Exception:
    pass # Tolérance si la page tente de se recharger

# --- 2. BOUCLIER ANTI-CRASH GLOBAL ---
try:
    import google.generativeai as genai
    import datetime
    import traceback
    from io import BytesIO

    # --- VÉRIFICATION DES MODULES ---
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

    # --- MOTEUR DE GÉNÉRATION V33.1 (TRANSFERT & POWERPOINT) ---
    def forger_cours_v33(formation, sujet, lieu, moteur, api_key):
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(moteur)
        
        prompt = f"""
        Tu es l'ingénieur pédagogique expert du CFA Interpro de Chartres. 
        Module de 60 minutes. Formation : {formation}. Sujet : {sujet}. 
        Localisation : {lieu} (Chartres/Champhol).
        
        EXIGENCES V33.1 :
        1. Ton ludique, humour technique et jeux de mots. Aucune formule de salutation au début du cours.
        2. SECTION TRANSFERT : "Et si la situation changeait ?". Propose une variante du scénario avec une contrainte supplémentaire (ex: panne inédite, client difficile).
        3. ACCOMPAGNEMENT POWERPOINT : Intègre une description des diapositives avec des idées de visuels (photos réelles ET dessins style 'cartoons' aux couleurs vives) pour un visionnage plaisant et non académique.
        4. STRUCTURE EXHAUSTIVE : 
           - # 🎓 TITRE DU MODULE
           - ## 🎯 RÉFÉRENTIEL MÉTIER
           - ## 🎬 SCÉNARIO PRINCIPAL (Humour local)
           - ## 📖 CŒUR TECHNIQUE CERTIFIÉ (Logique argumentée)
           - ## 🔄 ET SI LA SITUATION CHANGEAIT ?
           - ## 📝 ÉVALUATION SOMMATIVE (/20)
           - ## 👨‍🏫 CORRECTION & AUTO-CRITIQUE (Justification des réponses)
           - ## 🖥️ STRUCTURE POUR DIAPORAMA
        5. Ne cite JAMAIS 'Manu' dans le cours.
        """
        return model.generate_content(prompt).text

    # --- EXPORT WORD V33.1 ---
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
                    p.runs[0].font.color.rgb = RGBColor(0, 153, 153) # Cyan
                elif "DIAPORAMA" in ligne:
                    p.runs[0].font.color.rgb = RGBColor(204, 102, 0) # Orange vif
            else:
                doc.add_paragraph(ligne)
                
        buf = BytesIO()
        doc.save(buf)
        return buf.getvalue()

    # --- INTERFACE ---
    st.title("⚡ EduForge Pro : V33.1 (Anti-Crash & Visuels)")
    st.markdown("*L'ingénierie qui prépare les apprentis aux imprévus du métier - Chartres*")

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
        
        # CORRECTIF ANTI-CRASH : Clé statique pour le bouton
        if st.button("🚀 Forger le Module", key="btn_forge_v33_1"):
            if api_key and sujet_in:
                with st.spinner("Analyse des compétences, transfert et création des visuels..."):
                    res = forger_cours_v33(f_sel, sujet_in, lieu_in, moteur, api_key)
                    st.session_state.cours_memoire = res
                    st.session_state.sujet_memoire = sujet_in

    # CORRECTIF ANTI-CRASH : Ancrage du conteneur d'affichage avant la condition
    result_container = st.container()

    with result_container:
        # --- AFFICHAGE ---
        if st.session_state.cours_memoire:
            col_t, col_dl = st.columns([4, 1])
            with col_t:
                st.success(f"✅ Module '{st.session_state.sujet_memoire}' forgé avec scénario de transfert et diaporama.")
            with col_dl:
                if HAS_DOCX:
                    data = generer_docx_v33(st.session_state.sujet_memoire, st.session_state.cours_memoire)
                    # Clé de téléchargement sécurisée
                    st.download_button("📥 WORD", data, f"Cours_{st.session_state.sujet_memoire}.docx", key="dl_v33_master")
            
            st.divider()
            st.markdown(st.session_state.cours_memoire)

# --- FIN DU BOUCLIER (CAPTURE DES ERREURS TECHNIQUES) ---
except Exception as e:
    st.error("🚨 DÉFAILLANCE CRITIQUE INTERCEPTÉE PAR LA BOÎTE NOIRE")
    st.warning("L'application a évité le crash complet. Voici le rapport technique à me transmettre :")
    st.code(traceback.format_exc())
