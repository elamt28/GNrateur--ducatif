import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import InvalidArgument, ResourceExhausted

# --- CONFIGURATION EXPERTE ---
st.set_page_config(page_title="GNrateur contenu éducatif", layout="wide", page_icon="📝")

# --- MOTEUR DE GÉNÉRATION ROBUSTE (TEXTE STRUCTURÉ) ---
def generer_cours_complet(formation, sujet, localisation):
    """
    Génère un cours complet en Markdown. 
    L'avantage du Markdown est qu'il ne plante JAMAIS (contrairement au JSON) 
    et se copie/colle parfaitement dans Word.
    """
    moteur = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods][0]
    model = genai.GenerativeModel(moteur)
    
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

# --- INTERFACE UTILISATEUR ---
st.title("📝 GNrateur contenu éducatif")
st.markdown("L'outil d'ingénierie pédagogique infaillible du CFA. Générez des documents structurés, conformes et prêts à imprimer.")

with st.sidebar:
    st.header("🔑 Accès Sécurisé")
    st.markdown("[Obtenir une clé API gratuite ici](https://aistudio.google.com/app/apikey)")
    api_key = st.text_input("Clé API Google Gemini :", type="password", help="Insérez votre clé API valide ici. Elle n'est pas sauvegardée et reste locale.")
    
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
    elif not formation:
         st.warning("Veuillez indiquer une formation concernée.")
         st.stop()
    elif not sujet:
        st.warning("Veuillez indiquer un sujet de cours.")
        st.stop()
    else:
        # Configuration de la clé saisie par l'utilisateur
        genai.configure(api_key=api_key)
        
        with st.spinner("Rédaction du document clef en main (Processus blindé en cours)..."):
            try:
                # 1. Génération du contenu brut
                document_cours = generer_cours_complet(formation, sujet, localisation)
                
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
                # Analyse de l'erreur pour donner une estimation de temps
                error_msg = str(e)
                if "retry in" in error_msg:
                    try:
                        # Tente d'extraire le temps d'attente suggéré par Google
                        time_str = error_msg.split("retry in ")[1].split("s")[0]
                        wait_time = int(float(time_str)) + 1 # Arrondi au supérieur
                        st.warning(f"⏱️ Quota d'utilisation dépassé (Erreur 429). Limite de requêtes par minute atteinte. Veuillez patienter environ {wait_time} secondes avant de relancer.")
                    except:
                         st.warning("⏱️ Quota d'utilisation dépassé (Erreur 429). Limite de requêtes atteinte. Veuillez patienter environ une minute avant de relancer.")
                else:
                    st.warning("⏱️ Quota d'utilisation dépassé (Erreur 429). Vous avez peut-être atteint votre limite journalière. Vérifiez votre quota sur Google AI Studio.")
            except Exception as e:
                # Traitement des autres erreurs imprévues (réseau, surcharge serveur...)
                error_message = str(e)
                if "API_KEY_INVALID" in error_message:
                    st.error("🚨 Clé API refusée par le serveur Google. Vérifiez votre clé.")
                elif "429" in error_message or "quota" in error_message.lower():
                     # Fallback si l'exception n'est pas captée comme ResourceExhausted
                    st.warning("⏱️ Quota d'utilisation gratuit dépassé. Veuillez patienter avant de relancer.")
                else:
                    st.error("🚨 Une erreur de connexion au serveur est survenue. Veuillez réessayer dans quelques instants.")
                    st.code(error_message)
