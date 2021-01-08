import requests
import streamlit as st


def render_trust(globals):

    st.write("Assess trust score of information")
    st.subheader(
        "STEP 5: Use text insights to check for trustworthiness of information"
    )
    st.write(globals["text"])

    return globals
