import requests
import streamlit as st

full_pipeline = [
    "cleaner",
    "tagger",
    "sentencizer",
    "parser",
    "ner",
    "summarizer",
    "rouge_scorer",
    "health_analyzer",
    "readability",
    "report_collector",
    "story_generator",
]

health_analyzer_pipeline = [
    "tagger",
    "sentencizer",
    "parser",
    "ner",
    "health_analyzer",
    "report_collector",
]


def _run_pipeline(base_url, text, meta, settings):
    url = f"{base_url}/pipeline/default"
    data = {"text": text, "meta": meta, "settings": settings}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
    else:
        result = {"text": f"<Error: {response}>", "meta": {}}
    return result


def render_ner(globals):

    base_url = str(globals["api_endpoint"])
    # api_key = str(globals["api_key"])
    text = globals["text"]
    meta = globals["meta"]

    st.write("Analyze medical and other named entities and concepts")
    st.subheader(
        "STEP 4: run default pipeline incl. Entitiy recognition and Azure TA for Health"
    )
    st.write(text)

    settings = {"enable": health_analyzer_pipeline}
    result = _run_pipeline(base_url, text, meta, settings)

    st.write(result)

    return globals
