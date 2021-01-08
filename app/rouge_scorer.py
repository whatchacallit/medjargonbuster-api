import app
import logging
from spacy.language import Language
from spacy.tokens import Doc
from rouge_score import rouge_scorer


log = logging.getLogger(__name__)

from app.models import PIPELINE_STAGES as STAGE


class RougeScorer(object):
    """
    Calculates the ROUGE scores of the summary.
    Ignored if no summary has been generated (doc._.summary_sentences)
    """

    name = STAGE.ROUGE_SCORER
    nlp: Language = None

    def __init__(self, nlp):
        self.nlp = nlp

    def __call__(self, doc):
        if not doc.has_extension(STAGE.SUMMARIZER):
            log.warning(
                f"The 'summarizer' pipeline stage did not run, can't calculate ROUGE scores"
            )
            return
        elif not doc.has_extension(self.name):
            doc.set_extension(self.name, getter=self._calculate_rouge_scores)

        return doc

    def _calculate_rouge_scores(self, doc):
        assert doc.has_extension(STAGE.SUMMARIZER)
        assert doc.has_extension(STAGE.ROUGE_SCORER)

        summary_sentences = [str(s) for s in doc._.summarizer]
        summaryText = "\n".join([str(s) for s in summary_sentences])

        # TODO stemmer? multi-language ?
        scorer = rouge_scorer.RougeScorer(
            ["rouge1", "rouge2", "rougeL"], use_stemmer=True
        )

        # We score the original (cleaned) text against the summary.
        # As we do extractive summarization and non-destructive cleaning, "precision" should always be 1.0
        # (e.g. summary only contains text from the original)
        # The "recall" is actually interesting, as it measures how many n-grams from the original text are still
        # covered in the summary. We probably want to maximize this (while keeping the summary as short as possible)
        score_result = scorer.score(str(doc.text), summaryText)

        return score_result
