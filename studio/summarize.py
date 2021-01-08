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

summary_pipeline = [
    "sentencizer",
    "summarizer",
    "rouge_scorer",
    "readability",
    "report_collector",
]


def render_summarize(globals):

    base_url = str(globals["api_endpoint"])
    api_key = str(globals["api_key"])
    text = globals["text"]
    meta = globals["meta"]
    # pre-select the stages with defaults
    enabled_stages = {}
    for stage in full_pipeline:
        enabled_stages[stage] = st.checkbox(stage, value=(stage in summary_pipeline))

    settings = {
        "enable": [stage for stage, enabled in enabled_stages.items() if enabled]
    }

    st.write("Generate Summary from text")
    st.subheader("STEP 3: run default pipeline on text")
    # st.write(text)

    # TODO Configure settings here

    if st.button("Run Analysis"):
        url = f"{base_url}/pipeline/default"
        data = {"text": text, "meta": meta, "settings": settings}
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
        else:
            result = {"text": f"<Error: {response}>", "meta": {}}

        # st.write(result.get("meta"))
        st.markdown("---")
        meta = result["meta"]

        summary_text = meta["summaryText"]
        summary_factor = (len(summary_text) / len(result["text"])) * 100

        readability_score = meta["readability"]
        rouge_recall = meta["summary_rouge_recall"]

        st.subheader("Extractive Summary")
        st.markdown(
            f"Summary length is **{summary_factor:.2f}%** of original text, with a _ROUGE-L recall_ of **{rouge_recall['rougeL']*100:.2f}%** \
            and a _Dale-Chall_ readability score of \
            **{readability_score['text']['dale_chall']:.2f}** (summary) and \
            **{readability_score['summary']['dale_chall']:.2f}** (original text)"
        )

        st.text_area(label="Summary (5 sentences)", value=summary_text, height=450)

        st.write(meta)

    return globals
