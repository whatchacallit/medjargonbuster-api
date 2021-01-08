import app
import logging


log = logging.getLogger(__name__)

from app.models import PIPELINE_STAGES as STAGE


# from string import punctuation

from spacy.language import Language
from spacy.tokens import Doc

# import spacy
# from spacy.lang.en.stop_words import STOP_WORDS  # TODO how to handle other languages?
# from spacy import tokens


# 3rd party lib for summarization: gensim
from gensim.summarization.summarizer import summarize as gensim_summarize


class Summarizer(object):
    nlp = None
    num_sentences = 5

    def __init__(self, nlp: Language, num_sentences=5):
        self.nlp = nlp
        self.num_sentences = num_sentences

    def __call__(self, doc: Doc):
        if not doc.has_extension(STAGE.SUMMARIZER):
            doc.set_extension(STAGE.SUMMARIZER, getter=self._summarize)

        return doc

    def _summarize(self, doc: Doc):
        assert doc.has_extension(STAGE.SUMMARIZER)

        summary_modes = {
            "gensim": self._createSummaryWithGensim,
        }
        selected_mode = "gensim"  # for now, the only one that produces ok results
        summary_sentences = summary_modes.get(selected_mode, "gensim")(doc)

        return summary_sentences[0 : self.num_sentences]

    def filter_for_summarize(self, sentences):
        """
        Tries to filter out detected "sentences" that will not be good candidates
        for extractive summarization.
        """
        filtered = []
        for sentence in sentences:
            tokens = sentence.doc[sentence.start : sentence.end]
            words = [
                t for t in tokens if not t.is_space and not t.is_stop and not t.is_punct
            ]
            stop_words = [t for t in tokens if t.is_stop]
            punkts = [t for t in tokens if t.is_punct]

            # Rule: at least n word (chunks?)
            min_words = 2
            if len(words) < min_words:
                continue
            # Rule: at most m words
            max_chars = 200
            if len(sentence) > max_chars:
                continue

            # Rule: need to have at least one stop word. PROBLEM: sentencizer cuts off parts into 2 sentences
            if len(stop_words) < 1:
                continue
            # Rule: not more punctiation than words
            if len(punkts) > len(words):
                continue
            # Rule: needs to have subject, predicate, object
            # Rule: needs more word chars than no-word chars
            # Rule: does look like a "citation" ?

            # If we made it to here, consider the sentence a potentical candidate for summarization
            filtered.append(sentence)

        return filtered

    def _createSummaryWithGensim(self, doc):
        #
        # We use Gensim TextRank for extractive text summarization.
        # TODO: Explore other algorithms and options, filter candidate sentences,
        # use spaCy sentencizer for better results  etc...
        text = str(
            doc.text
        )  # "".join([str(s.text) for s in self.filter_for_summarize(doc.sents)])

        summarySentences = gensim_summarize(
            text=text,
            # ratio=0.1,
            word_count=200,
            split=True,
        )

        return summarySentences
