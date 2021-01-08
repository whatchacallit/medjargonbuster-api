import requests
import streamlit as st
from streamlit.uploaded_file_manager import UploadedFile

# Global vars from main page
GLOBALS = {}


@st.cache
def _extract_text(fileObj_or_url):
    r = None

    base_url = str(GLOBALS["api_endpoint"])
    # api_key = str(GLOBALS["api_key"])

    if isinstance(fileObj_or_url, str):
        url = f"{base_url}/extract"
        r = requests.get(url, params={"url": fileObj_or_url})
    else:
        url = f"{base_url}/extract/upload"
        files = {"file": fileObj_or_url}
        r = requests.post(url, files=files)

    if r.status_code == 200:
        d = r.json()
        result = {"text": str(d["text"]), "meta": d["meta"]}

    else:
        result = {"text": f"<an error occured: {str(r)}>", "meta": {}}

    return result


def _clean_extracted_text(raw, metadata):
    base_url = str(GLOBALS["api_endpoint"])
    # api_key = str(GLOBALS["api_key"])

    url = f"{base_url}/pipeline/default"

    data = {"text": raw, "meta": metadata, "settings": {"clean_only": True}}

    r = requests.post(url, json=data)

    if r.status_code == 200:
        return r.json()
    else:
        return {"text": f"An error occured: {str(r.text)}", "time": -1}


def render_extract(globals):
    global GLOBALS
    GLOBALS = globals

    st.write(
        "Text extraction and pre-processing is essential for all other steps later."
    )

    result = None

    doc_file: UploadedFile = st.file_uploader(
        "Upload document file",
        type=[
            "pdf",
            "doc",
            "docx",
            "txt",
            "jpg",
            "jpeg",
            "png",
            "gif",
            "tiff",
            "ppt",
            "pptx",
        ],
    )
    demo_url = "https://www.cancertherapyadvisor.com/home/cancer-topics/breast-cancer/breast-cancer-black-female-patient-tool-may-overlook-risk/"
    st.markdown(
        f"Alternativly, you can also directly extract from any public url, e.g.\n _{demo_url}_"
    )
    doc_url = st.text_input(f"URL to a document, news article, wikipedia, blog ... ")

    st.markdown("---")
    st.subheader("STEP 1: Results from text extraction")

    if doc_file is not None:
        st.write("You uploaded a file to analyze")
        doc_details = {
            "Filename": doc_file.name,
            "FileType": doc_file.type,
            "FileSize": doc_file.size,
        }
        st.write(doc_details)

        # Load file
        result = _extract_text(doc_file)
    elif doc_url:
        st.write(f"Extracting text from url: {doc_url}")
        result = _extract_text(doc_url)

    if result is not None:
        # show raw extracted text
        extracted_text = st.text_area(
            "Extracted (raw) text", height=300, value=result["text"]
        )
        # Show metadata
        extractor = result["meta"].get("extractor", "unknown")
        source = result["meta"].get("source", "unknown")
        contenttype = result["meta"].get("Content-Type", "unknown")
        language = result["meta"].get("language", "unknown")

        st.markdown(
            f"The system used the **'{extractor}'** extractor for this **'{source}'** document with content-type **'{contenttype}'**. \
            We think the language is **'{language}'**"
        )

        st.write(
            "Extracted metadata (depends on document type / extractor used): ",
            result["meta"],
        )

        st.markdown("---")
        st.subheader("STEP 2: Clean the extracted text for further processing")
        st.write(
            "Clean and preprocess the text. Ideally we get a full text of well-formed sentences. "
        )
        result = _clean_extracted_text(extracted_text, result["meta"])
        clean_text = st.text_area("Clean text", height=300, value=result["text"])
        clean_meta = st.write(result["meta"])

        # remember the state
        GLOBALS["text"] = result["text"]
        GLOBALS["meta"] = result["meta"]

        return GLOBALS

    else:
        st.write("Please upload a file first or specify an URL for further analysis")

    return GLOBALS
