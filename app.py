import streamlit as st
import openai
from pypdf import PdfReader
import docx
import pandas as pd
from pptx import Presentation

# Configuration de la page
st.set_page_config(
    page_title="AI Document Summarizer",
    page_icon="📄",
    layout="wide"
)

# Configuration d'OpenAI avec la clé API depuis les secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

def extract_text_from_pdf(file):
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Erreur lors de la lecture du PDF: {str(e)}")
        return None

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Erreur lors de la lecture du DOCX: {str(e)}")
        return None

def extract_text_from_excel(file):
    try:
        df = pd.read_excel(file)
        text = "Colonnes : " + ", ".join(df.columns) + "\n\n"
        text += f"Nombre de lignes : {len(df)}\n"
        text += "Aperçu des données :\n"
        text += df.head().to_string()
        return text
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier Excel: {str(e)}")
        return None

def extract_text_from_pptx(file):
    try:
        prs = Presentation(file)
        text = ""
        for i, slide in enumerate(prs.slides, 1):
            text += f"\nDiapositive {i}:\n"
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text
    except Exception as e:
        st.error(f"Erreur lors de la lecture du PowerPoint: {str(e)}")
        return None

def get_file_content(uploaded_file):
    if uploaded_file is None:
        return None
    
    try:
        file_type = uploaded_file.type
        if file_type == "application/pdf":
            return extract_text_from_pdf(uploaded_file)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_text_from_docx(uploaded_file)
        elif file_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            return extract_text_from_excel(uploaded_file)
        elif file_type in ["application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation"]:
            return extract_text_from_pptx(uploaded_file)
        else:
            return uploaded_file.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {str(e)}")
        return None

def get_summary(text, summary_type, target_language, max_length):
    if not text:
        return None
    
    try:
        # Préparation du prompt selon le type de résumé
        prompts = {
            "vulgarized": f"Résume ce texte de manière simple et accessible en {target_language} (~{max_length} mots) :\n\n{text}",
            "technical": f"Fais un résumé technique de ce texte en {target_language}, en te concentrant sur les aspects techniques (~{max_length} mots) :\n\n{text}",
            "bullets": f"Liste les points clés de ce texte en {target_language} (maximum {max_length} points) :\n\n{text}",
            "executive": f"Crée un executive summary de ce texte en {target_language} (~{max_length} mots) :\n\n{text}"
        }

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un expert en résumé et synthèse de documents."},
                {"role": "user", "content": prompts[summary_type]}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Erreur lors de la génération du résumé : {str(e)}")
        return None

def main():
    st.title("📄 AI Document Summarizer")

    # Configuration dans la barre latérale
    with st.sidebar:
        st.header("Paramètres")
        
        target_language = st.selectbox(
            "Langue du résumé",
            ["français", "anglais", "espagnol", "allemand"],
            index=0
        )
        
        summary_type = st.selectbox(
            "Type de résumé",
            ["vulgarized", "technical", "bullets", "executive"],
            format_func=lambda x: {
                "vulgarized": "Vulgarisé",
                "technical": "Technique",
                "bullets": "Points clés",
                "executive": "Executive Summary"
            }[x]
        )
        
        max_length = st.slider(
            "Longueur approximative",
            min_value=100,
            max_value=1000,
            value=300,
            step=50
        )

    # Zone principale
    source_type = st.radio(
        "Source du texte",
        ["Fichier", "Texte direct"],
        horizontal=True
    )

    # Gestion de l'entrée
    text = None
    if source_type == "Fichier":
        file = st.file_uploader(
            "Choisissez un fichier",
            type=["txt", "pdf", "docx", "xlsx", "xls", "pptx", "ppt"]
        )
        if file:
            text = get_file_content(file)
    else:
        text = st.text_area(
            "Collez votre texte ici",
            height=200
        )

    # Affichage et traitement
    if text:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Document original")
            with st.expander("Voir le contenu", expanded=False):
                st.text_area("", text, height=400)

        if st.button("Générer le résumé", type="primary"):
            with st.spinner("Génération du résumé..."):
                summary = get_summary(text, summary_type, target_language, max_length)
                
                if summary:
                    with col2:
                        st.subheader("Résumé")
                        st.markdown(summary)
                        
                        st.download_button(
                            "📥 Télécharger le résumé",
                            summary,
                            "resume.txt",
                            "text/plain",
                            use_container_width=True
                        )

if __name__ == "__main__":
    main()
