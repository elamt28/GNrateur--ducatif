import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import InvalidArgument, ResourceExhausted
import json
import os
import datetime
from io import BytesIO

# --- VÉRIFICATION DES MODULES (SÉCURITÉ ANTI-CRASH) ---
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

# --- CONFIGURATION DES VARIABLES GLOBALES ET FIREBASE ---
APP_ID = globals().get('__app_id', 'eduforge-pro-master-cfa')
FIREBASE_CONFIG = globals().get('__firebase_config')

# --- INITIALISATION DU STOCKAGE SÉCURISÉ (RÈGLE 3) ---
def init_storage():
    if not HAS_FIREBASE or not FIREBASE_CONFIG:
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

# --- FONCTION DE NETTOYAGE (ANTI-CRASH V21.1) ---
def nettoyer_texte_pour_export(texte):
    """Nettoie les caractères spéciaux qui pourraient faire planter l'export."""
    if not texte: return ""
    return str(texte).replace('’', "'").replace('œ', 'oe').replace('€', 'Euros')

# --- GESTION DE L'HISTORIQUE (RÈGLES 1 & 2) ---
def sauvegarder_dans_historique(formation, sujet, contenu):
    """Sauvegarde le cours dans Firestore pour consultation sur Pixel 9 et PC."""
    if not db: return
    try:
        # RÈGLE 1 : Chemin public /artifacts/{appId}/public/data/{collection}
        doc_ref = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('historique').document()
        doc_ref.set({
            'formation': formation,
            'sujet': sujet,
            'contenu': contenu,
            'date': datetime.datetime.now(),
            'timestamp': datetime.datetime.now().timestamp()
        })
    except Exception: pass

def recuperer_historique():
    """Récupère tous les cours de ta bibliothèque."""
    if not db: return []
    try:
        # RÈGLE 2 : Requête simple, tri manuel en mémoire Python
        docs = db.collection('artifacts').document(APP_ID).collection('public').document('data').collection('historique').stream()
        results = [doc.to_dict() for doc in docs]
        results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return results
    except Exception: return []

# --- OUTILS D'EXPORT ---
def generer_docx(titre, contenu):
    """Génère un document Word propre pour l'impression au CFA."""
    if not HAS_DOCX: return None
    doc = Document()
    # Nettoyage préventif
    titre_nettoyé = nettoyer_texte_pour_export(titre)
    contenu_nettoyé = nettoyer_texte_pour_export(contenu)
    
    header = doc.add_heading(titre_nettoyé, 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lignes = contenu_nettoyé.split('\n')
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
    """Génère un QR Code pour rendre tes cours interactifs."""
    if not HAS_QR: return None
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

# --- MOTEURS D'INTELLIGENCE ARTIFICIELLE ---
def suggerer_sujets(formation, api_key):
    """Utilise gemini-1.5-flash pour économiser ton quota quotidien."""
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Expert pédagogique CFA Chartres : Propose 5 sujets techniques originaux et certifiés conformes pour la formation {formation}. Liste à puces."
        reponse = model.generate_content(prompt)
        return reponse.text
    except Exception as e: return f"Erreur de suggestion : {e}"

def generer_cours_complet(formation, sujet, localisation, moteur_choisi):
    """Génère un cours de 60 minutes avec évaluation sur 20."""
    model = genai.GenerativeModel(moteur_choisi)
    prompt = f"""
    Tu es le meilleur expert ingénieur pédagogique du CFA Interpro de Chartres. 
    Rédige un cours passionnant de 60 minutes pour des apprentis.
    
    PARAMÈTRES :
    - Formation : {formation}
    - Sujet : {sujet}
    - Lieu : {localisation} (Aux alentours de Chartres/Champhol)
    
    CONSIGNES STRICTES :
    1. Ton ludique, humour, jeux de mots techniques (ex: 'Marche ou crêpes').
    2. Ne cite JAMAIS le prénom 'Manu' dans le cours.
    3. PAS DE DESCRIPTIONS VISUELLES ni d'images. Uniquement du texte pédagogique.
    4. Vocabulaire technique exigeant et certifié exact.
    
    STRUCTURE :
    # 🎓 Cours : {sujet}
    **Formation :** {formation} | **Lieu :** {localisation}
    ## 🎯 Référentiel visé (Compétences/Savoirs officiels)
    ## 🎬 Scénario Pédagogique (Ancrage local Chartres/Champhol avec humour)
    ## 📖 Notions Clés & Mission (Cœur technique certifié)
    ## 🧠 Activités FOAD (QCM, Vrai/Faux, Association)
    ## 📝 Évaluation Somative (Sur 20 points avec barème détaillé)
    ---
    ## 👨‍🏫 ESPACE FORMATEUR (Corrections certifiées et conseils de notation)
    """
    reponse = model.generate_content(prompt)
    return reponse.text

@st.cache_data(show_spinner=False)
def obtenir_modeles_disponibles(api_key):
    """Récupère les moteurs actifs."""
    genai.configure(api_key=api_key)
    try:
        return [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except: return ["gemini-1.5-flash", "gemini-2.5-flash"]

# --- INTERFACE UTILISATEUR STREAMLIT ---
st.title("⚡ EduForge Pro : Code Maître")
st.markdown("**L'expertise pédagogique certifiée du CFA Interpro de Chartres**")

tab_gen, tab_hist = st.tabs(["🚀 Forger un Cours", "📚 Bibliothèque Personnelle"])

with st.sidebar:
    st.header("🔑 Accès API")
    st.markdown("[Obtenir une clé gratuite](https://aistudio.google.com/app/apikey)")
    api_key = st.text_input("Clé Google Gemini :", type="password")
    if api_key:
        liste_moteurs = obtenir_modeles_disponibles(api_key)
        moteur_ia = st.selectbox("Moteur IA (Préférer 1.5-flash en cas d'erreur 429) :", liste_moteurs)
    else: moteur_ia = None

with tab_gen:
    st.header("⚙️ Paramètres")
    options_f = [
        "Bac Pro Maintenance Véhicule (2de)", "Bac Pro Maintenance Véhicule (1re)", "Bac Pro Maintenance Véhicule (Term)",
        "BTS Maintenance Véhicule", "Carrossier/Peintre", "BP Boulanger", "BM Boulanger", "BP Boucher", 
        "CAP Équipier Polyvalent du Commerce (EPC)", "BP Coiffure", "AMLHR", "➕ Autre"
    ]
    formation_sel = st.selectbox("Formation concernée :", options_f)
    formation = st.text_input("Précisez la formation :") if formation_sel == "➕ Autre" else formation_sel
    
    if st.button("💡 Suggérer des idées de sujets"):
        if api_key and formation: 
            with st.spinner("Consultation des référentiels..."):
                st.info(suggerer_sujets(formation, api_key))
            
    sujet = st.text_input("Sujet du cours :", placeholder="Ex: L'allumage électronique, Levains naturels...")
    lieu = st.text_input("Lieu du scénario :", value="Chartres / Champhol")
    lancer = st.button("🚀 Forger le Module", use_container_width=True)

    if lancer and sujet and moteur_ia:
        genai.configure(api_key=api_key)
        with st.spinner(f"Forgeage pédagogique avec {moteur_ia} en cours..."):
            try:
                document_cours = generer_cours_complet(formation, sujet, lieu, moteur_ia)
                # Sauvegarde automatique dans Firestore
                sauvegarder_dans_historique(formation, sujet, document_cours)
                
                st.success("✅ Module pédagogique forgé et archivé !")
                col1, col2 = st.columns([2, 1])
                with col1:
                    if HAS_DOCX: 
                        st.download_button("📥 Télécharger en format WORD (.docx)", generer_docx(f"Cours : {sujet}", document_cours), f"Cours_{sujet}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                with col2:
                    if HAS_QR: 
                        st.image(generer_qr_code("https://www.cfa-interpro-28.fr/"), width=120, caption="Lien de session")
                
                st.divider()
                st.markdown(document_cours)
            except ResourceExhausted: 
                st.error("🚨 Quota atteint. Changez de moteur IA ou attendez 60 secondes.")
            except Exception as e: 
                st.error(f"🚨 Une erreur est survenue : {e}")

with tab_hist:
    st.header("📂 Bibliothèque Pédagogique")
    if not HAS_FIREBASE or not db: 
        st.warning("⚠️ Sauvegarde indisponible (Module manquant). Vérifiez votre fichier requirements.txt.")
    else:
        archives = recuperer_historique()
        if not archives: 
            st.info("Votre bibliothèque est vide. Forgez votre premier cours !")
        else:
            for item in archives:
                date_val = item.get('date')
                date_str = date_val.strftime('%d/%m/%Y %H:%M') if date_val else "Inconnue"
                with st.expander(f"📅 {date_str} | {item.get('formation')} : {item.get('sujet')}"):
                    st.markdown(item.get('contenu'))
                    if HAS_DOCX:
                        st.download_button("📥 Retélécharger WORD", generer_docx(item.get('sujet'), item.get('contenu')), f"Archive_{item.get('sujet')}.docx", key=f"dl_{item.get('timestamp')}")
