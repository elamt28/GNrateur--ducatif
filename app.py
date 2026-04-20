import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import InvalidArgument, ResourceExhausted
import json
import os
import datetime
from io import BytesIO

# --- VÉRIFICATION DES MODULES (ANTI-CRASH) ---
try:
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False

# --- CONFIGURATION DES VARIABLES GLOBALES ---
# Utilisation de l'identifiant d'application fourni par l'environnement
APP_ID = globals().get('__app_id', 'gnrateur-educatif-cfa')
FIREBASE_CONFIG = globals().get('__firebase_config')

# --- INITIALISATION DU STOCKAGE (SÉCURISÉ - RÈGLE 3) ---
def init_storage():
    if not HAS_FIREBASE or not FIREBASE_CONFIG:
        return None
    try:
        if not firebase_admin._apps:
            conf = json.loads(FIREBASE_CONFIG)
            cred = credentials.Certificate(conf)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        return None

db = init_storage()

# --- FONCTIONS DE SAUVEGARDE ET RÉCUPÉRATION (RÈGLES 1 & 2) ---
def sauvegarder_dans_historique(formation, sujet, contenu):
    if not db:
        return
    try:
        # RÈGLE 1 : Chemin strict /artifacts/{appId}/public/data/{collectionName}
        doc_ref = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('historique').document()
        doc_ref.set({
            'formation': formation,
            'sujet': sujet,
            'contenu': contenu,
            'date': datetime.datetime.now(),
            'timestamp': datetime.datetime.now().timestamp()
        })
    except Exception:
        pass

def recuperer_historique():
    if not db:
        return []
    try:
        # RÈGLE 2 : Requête simple, tri en mémoire Python
        docs = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('historique').stream()
        results = [doc.to_dict() for doc in docs]
        # Tri par date décroissante (plus récent en premier)
        results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return results
    except Exception:
        return []

# --- FONCTIONS EXPORT ET UTILITAIRES ---
def generer_docx(titre, contenu):
    if not HAS_DOCX:
        return None
    doc = Document()
    # Titre centré
    header = doc.add_heading(titre, 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    lignes = contenu.split('\n')
    for ligne in lignes:
        if ligne.startswith('# '): 
            doc.add_heading(ligne.replace('# ', ''), level=1)
        elif ligne.startswith('## '): 
            doc.add_heading(ligne.replace('## ', ''), level=2)
        elif ligne.startswith('### '): 
            doc.add_heading(ligne.replace('### ', ''), level=3)
        elif ligne.startswith('**'):
            p = doc.add_paragraph()
            p.add_run(ligne.replace('**', '')).bold = True
        else: 
            doc.add_paragraph(ligne)
            
    output = BytesIO()
    doc.save(output)
    return output.getvalue()

def generer_qr_code(url):
    if not HAS_QR:
        return None
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

def suggerer_sujets(formation, api_key):
    genai.configure(api_key=api_key)
    try:
        model_name = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods][0]
        model = genai.GenerativeModel(model_name)
        prompt = f"Expert pédagogique CFA Chartres : Propose 5 sujets techniques pour {formation}. Liste à puces."
        reponse = model.generate_content(prompt)
        return reponse.text
    except Exception as e:
        return f"Erreur de suggestion : {e}"

def generer_cours_complet(formation, sujet, localisation, moteur_choisi):
    model = genai.GenerativeModel(moteur_choisi)
    prompt = f"""
    Tu es le meilleur expert ingénieur pédagogique. Rédige un document de cours "clef en main" pour des apprentis.
    
    PARAMÈTRES :
    - Formation visée : {formation}
    - Sujet du cours : {sujet}
    - Localisation du scénario : {localisation} (Alentours de Chartres/Champhol)
    
    CONSIGNES STRICTES D'EXCELLENCE :
    1. Le ton doit être ludique, avec une pointe d'humour et des jeux de mots.
    2. Ne cite JAMAIS le prénom "Manu" dans le cours.
    3. La correction de TOUTES les activités doit IMPÉRATIVEMENT se trouver dans une section isolée, tout à la fin du document.
    4. Sois exigeant sur le vocabulaire technique adapté au niveau de la formation.
    
    STRUCTURE OBLIGATOIRE DU DOCUMENT :
    # 🎓 Cours : {sujet}
    **Formation :** {formation} | **Lieu du scénario :** {localisation}
    
    ## 🎯 Référentiel visé (Compétences et Savoirs)
    [Détaille ici les codes précis et descriptions des compétences concernées.]
    
    ## 🎬 Scénario Pédagogique
    [Une accroche ludique située localement.]
    
    ## 📖 Notions Clés & Mission
    [Le cœur technique du cours.]
    
    ## 🧠 Activités d'Entraînement
    - QCM (3 questions)
    - Vrai ou Faux (3 questions)
    - Jeu d'associations (4 mots/définitions)
    
    ## 📝 Évaluation Somative (Sur 20 points)
    [Une évaluation complète avec barème.]
    
    ---
    ## 👨‍🏫 ESPACE FORMATEUR (CORRECTIONS)
    [Corrections détaillées et barème de l'évaluation.]
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

# Alerte si les bibliothèques manquent
if not HAS_DOCX or not HAS_QR:
    st.error("🚨 ATTENTION : Votre fichier 'requirements.txt' est incomplet. L'export Word et le QR Code sont désactivés.")

tab_gen, tab_hist = st.tabs(["🚀 Nouveau Cours", "📚 Historique & Sauvegarde"])

with st.sidebar:
    st.header("🔑 Accès")
    st.markdown("[Clé API gratuite ici](https://aistudio.google.com/app/apikey)")
    api_key = st.text_input("Clé API Google Gemini :", type="password")
    st.divider()
    if api_key:
        liste_moteurs = obtenir_modeles_disponibles(api_key)
        moteur_ia = st.selectbox("Moteur IA :", liste_moteurs) if liste_moteurs else None
    else: moteur_ia = None

with tab_gen:
    st.header("⚙️ Paramètres de génération")
    options_formation = [
        "Bac Pro Maintenance Véhicule (2de)", "Bac Pro Maintenance Véhicule (1re)", "Bac Pro Maintenance Véhicule (Term)",
        "BTS Maintenance Véhicule", "Carrossier/Peintre", "BP Boulanger", "BM Boulanger", "BP Boucher", 
        "CAP EPC", "BP Coiffure", "AMLHR", "➕ Autre"
    ]
    formation_sel = st.selectbox("Formation :", options_formation)
    formation = st.text_input("Précisez la formation :") if formation_sel == "➕ Autre" else formation_sel
    
    if st.button("💡 Suggérer des idées de sujets"):
        if api_key and formation:
            st.info(suggerer_sujets(formation, api_key))
            
    sujet = st.text_input("Sujet du cours :", placeholder="Ex: Diagnostic ABS, Levains naturels...")
    localisation = st.text_input("Localisation :", value="Chartres / Champhol")
    lancer = st.button("🚀 Forger le Document", use_container_width=True)

    if lancer and sujet and moteur_ia:
        genai.configure(api_key=api_key)
        with st.spinner("Forgeage en cours..."):
            try:
                document_cours = generer_cours_complet(formation, sujet, localisation, moteur_ia)
                # Sauvegarde auto
                sauvegarder_dans_historique(formation, sujet, document_cours)
                
                st.success("✅ Document généré et sauvegardé !")
                col1, col2 = st.columns(2)
                with col1:
                    if HAS_DOCX:
                        docx_data = generer_docx(sujet, document_cours)
                        st.download_button("📥 Télécharger WORD", docx_data, f"Cours_{sujet}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                with col2:
                    if HAS_QR:
                        st.image(generer_qr_code("https://www.cfa-interpro-28.fr/"), width=100, caption="QR Code Session")
                
                st.divider()
                st.markdown(document_cours)
            except ResourceExhausted: 
                st.error("Quota dépassé. Attendez 1 min ou changez de moteur.")
            except Exception as e: 
                st.error(f"Erreur : {e}")

with tab_hist:
    st.header("📂 Vos archives pédagogiques")
    if not HAS_FIREBASE or not db:
        st.warning("⚠️ Sauvegarde indisponible (Module manquant).")
    else:
        historique = recuperer_historique()
        if not historique:
            st.info("Aucun cours en mémoire.")
        else:
            for item in historique:
                date_val = item.get('date')
                date_str = date_val.strftime('%d/%m/%Y %H:%M') if date_val else "Date inconnue"
                with st.expander(f"📅 {date_str} - {item.get('formation')} : {item.get('sujet')}"):
                    st.markdown(item.get('contenu'))
                    if HAS_DOCX:
                        docx_data = generer_docx(item.get('sujet'), item.get('contenu'))
                        st.download_button("📥 Retélécharger WORD", docx_data, f"Archive_{item.get('sujet')}.docx", key=f"dl_{item.get('timestamp')}")
