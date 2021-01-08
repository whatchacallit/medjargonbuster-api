import app
import logging
from typing import Counter
from spacy.language import Language


log = logging.getLogger(__name__)


from app.models import PIPELINE_STAGES as STAGE


class ReportCollector(object):
    """
    Collects all the results, metadata etc. from previous pipeline steps and condenses it into a
    format easily usable by the API
    """

    nlp: Language = None

    def __init__(self, nlp):
        self.nlp = nlp

    def __call__(self, doc):
        if not doc.has_extension(STAGE.REPORT_COLLECTOR):
            doc.set_extension(STAGE.REPORT_COLLECTOR, getter=self._collect)

        return doc

    def _collect(self, doc):
        assert doc.has_extension(STAGE.REPORT_COLLECTOR)

        # get pipeline steps/ registered extensions
        pipeline_names = self.nlp.pipe_names
        log.info(f"Collecting results from pipeline: {str(pipeline_names)}")

        # create the result object we'll append props to
        result = {"pipeline": pipeline_names}

        # Full (input) text and sentences
        if doc.is_sentenced:
            sentences = [sentence.text for sentence in doc.sents]
        else:
            sentences = []

        # all tokens that arent stop words or punctuations
        words = [
            token.text for token in doc if not token.is_stop and not token.is_punct
        ]
        # noun (or noun chunk!) tokens that arent stop words or punctuations
        nouns = [
            token.text
            for token in doc
            if not token.is_stop and not token.is_punct and token.pos_ == "NOUN"
        ]
        # Noun chunks (done by parser w. statistical model)
        if doc.is_parsed:
            result["noun_chunks"] = [token.text for token in doc.noun_chunks]
            result["num_noun_chunks"] = len(result["noun_chunks"])
            result["common_noun_chunks"] = Counter(result["noun_chunks"]).most_common(5)

        # merge into result...
        result = {
            **{
                "num_token": len(doc),
                "num_words": len(words),
                "num_sentences": len(sentences),
            },
            **result,
        }

        # five most common word tokens
        result["common_words"] = Counter(words).most_common(5)
        # five most common noun (chunk) tokens
        result["common_nouns"] = Counter(nouns).most_common(5)

        # NER: List of named entities, if "ner" pipe ran
        # see https://spacy.io/api/annotation#named-entities
        if doc.is_nered:
            entities = sorted(
                set([(entity.text, entity.label_) for entity in doc.ents])
            )
            result["named_entities"] = entities
            for label in [
                "ORG",
                "PERSON",
                "GPE",
                "WORK_OF_ART",
                "PRODUCT",
                "EVENT",
                "FAC",
                "NORP",
            ]:
                filtered_entities = [
                    entity.text for entity in doc.ents if entity.label_ == label
                ]
                result[label] = sorted(set(filtered_entities))
                result["common_" + label] = Counter(filtered_entities).most_common(5)

        # get the summary text, if "summarizer" pipe ran
        if doc.has_extension(STAGE.SUMMARIZER):
            summary_sents = [str(s) for s in doc._.summarizer]
            result["summary_sentences"] = summary_sents
            result["summaryText"] = "\n".join([str(s) for s in summary_sents])

        if STAGE.READABILITY in pipeline_names and doc.is_sentenced:
            # Readability scores (dale_chall/smog) for text and summary, if present.
            result["readability"] = doc._.get(STAGE.READABILITY)

        # rougeL-score for summary:
        # With extractive summarization, Precision should always be 1.0.
        # The Recall of 1/2/n-grams should give us the "n-gram coverage"
        # of the summary over the full text.
        # So we probably(?) want to optimize this coverage, balancing it with the summary length
        # TODO analyze deeper what we can deduct from that, what to optimize exactly (rouge1/2/L ?)
        if doc.has_extension(STAGE.ROUGE_SCORER) and doc.is_sentenced:
            d = doc._.get(STAGE.ROUGE_SCORER)
            result["summary_rouge_recall"] = {
                "rouge1": float(d["rouge1"].recall),
                "rouge2": float(d["rouge2"].recall),
                "rougeL": float(d["rougeL"].recall),
            }

        # Add the results from Azure Text Analytics fro Health
        if doc.has_extension(STAGE.HEALTH_ANALYZER):
            d = doc._.get(STAGE.HEALTH_ANALYZER)
            result[STAGE.HEALTH_ANALYZER] = d

        # remove all empty fields (e.g. keys with uncollected values)
        result = {k: v for k, v in result.items() if v}

        return result
