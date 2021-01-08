from studio.extract import render_extract
from studio.summarize import render_summarize
from studio.entity_recognition import render_ner
from studio.trust_score import render_trust
import pickle

import streamlit as st
import numpy as np
import pandas as pd
import requests
from streamlit.uploaded_file_manager import UploadedFile

# Store global settings from sidebar etc (like api endpoint) for easy access
GLOBALS = {}
GLOBALS_FILE = ".globals.pkl"


def _load_global_state():
    global GLOBALS
    try:
        infile = open(GLOBALS_FILE, "rb")
        GLOBALS = pickle.load(infile)
        if not GLOBALS:
            GLOBALS = {}
        infile.close()
    except:
        GLOBALS = {}
        pass


def _save_global_state():
    f = open(GLOBALS_FILE, "wb")
    pickle.dump(GLOBALS, f)
    f.close()


def main():
    """Med Jargon Buster Studio"""

    # st.title("Jargon Buster Backend Studio")
    # st.header("Tools to test and visualize backend services")
    global GLOBALS

    # Load GLOBALS from disk (Streamlit can't hold any state between re-runs for now)
    _load_global_state()

    activities = [
        "Extract and Preprocess",
        "Auto-Summarization",
        "Medical Entity Recognition",
        "Trust Score",
    ]

    # Build sidebar
    st.sidebar.markdown(
        "## Jargon Buster Studio\nPlease configure access and select your activities\n ---"
    )
    GLOBALS["api_endpoint"] = st.sidebar.text_input(
        key="api_endpoint", label="API endpoint", value="http://localhost:5000/api/v2"
    )
    GLOBALS["api_key"] = st.sidebar.text_input(key="api_key", label="API key", value="")

    choices = st.sidebar.selectbox("Select Activities", activities)

    # MAIN area
    st.subheader(choices)
    if choices == "Extract and Preprocess":
        GLOBALS = render_extract(GLOBALS)
    elif choices == "Auto-Summarization":
        GLOBALS = render_summarize(GLOBALS)
    elif choices == "Medical Entity Recognition":
        GLOBALS = render_ner(GLOBALS)
    elif choices == "Trust Score":
        GLOBALS = render_trust(GLOBALS)
    else:
        st.write(f"UNKNOWN activity: {choices}")

    if GLOBALS.get("text"):
        st.sidebar.write(f"Text extracted, {len(GLOBALS['text'])} chars")
    if GLOBALS.get("meta"):
        st.sidebar.write(f"Meta-data, {len(GLOBALS['meta'])} keys")

    # Save GLOBALS to disk (Streamlit can't hold any state between re-runs for now)
    _save_global_state()


if __name__ == "__main__":
    main()
