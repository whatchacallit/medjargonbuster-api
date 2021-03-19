from os import read
import app
import logging
from spacy.language import Language
from spacy.tokens import Doc
from spacy_readability import Readability

log = logging.getLogger(__name__)


from app.models import PIPELINE_STAGES as STAGE


class ReadabilityCalculator(object):
    """
    Calculates readability metrics for both full text and summary (if present)
    """

    nlp: Language = None
    summary_doc: Doc = None

    def __init__(self, nlp):
        self.nlp = nlp

    def __call__(self, doc: Doc):
        if not doc.has_extension(STAGE.READABILITY):
            doc.set_extension(STAGE.READABILITY, getter=self._calculate_readability)

        if doc.has_extension(STAGE.SUMMARIZER):
            # If the summarizer ran, we also calculate scores for the summary (not just fulltext)
            # spacy_readability needs a "Doc" object
            summary_sents = [str(s) for s in doc._.summarizer]

            summary_text = "\n".join([str(s) for s in summary_sents])

            # FIXME Sentencizer is needed by spacy_readability, but this here does not seem to work.
            # SMOG scores currently DON'T work !
            self.summary_doc = self.nlp.make_doc(summary_text)
            self.summary_doc = self.nlp.create_pipe("sentencizer")(self.summary_doc)

            # FIXME we could use the correct sentence boundaries to mark token.is_sent_start instead ?

        return doc

    def _calculate_readability(self, doc: Doc):
        """
        Call the readability score functions
        """
        assert doc.has_extension(STAGE.READABILITY)
        readability = Readability()
        scores = {"summary": {}, "text": {}}
        scores["text"]["dale_chall"] = readability.dale_chall(doc)
        scores["text"]["smog"] = readability.smog(doc)
        if self.summary_doc:
            scores["summary"]["dale_chall"] = readability.dale_chall(self.summary_doc)
            scores["summary"]["smog"] = readability.smog(self.summary_doc)

        return scores
