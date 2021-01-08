import app
import logging
from spacy.language import Language
from spacy.tokens import Doc

from textacy import preprocessing
import re

log = logging.getLogger(__name__)

from app.models import PIPELINE_STAGES as STAGE


class Cleaner(object):
    """
    Creates a new Doc with the text cleaned and normalized.
    TODO: Maybe add (optional) Spelling correction here, using a domain/language specific dictionary
    """

    nlp: Language = None

    def __init__(self, nlp):
        self.nlp = nlp

    def __call__(self, doc):
        if not doc.has_extension(STAGE.CLEANER):
            doc.set_extension(STAGE.CLEANER, getter=self._get_clean_info)

        new_text = self._clean(doc.text)
        new_doc = self.nlp.make_doc(new_text)  # need to re-Tokenize

        return new_doc

    def _get_clean_info(self, doc: Doc):
        return {"cleaning-profile": "default"}

    def _clean(self, text: str):
        txt = text.strip()

        #
        txt = preprocessing.normalize_unicode(txt, form="NFKC")

        # txt = preprocessing.remove_punctuation(txt)

        # Collapse whitespaces
        txt = preprocessing.normalize_whitespace(txt)
        # Remove newlines
        txt = preprocessing.normalize_repeating_chars(txt, chars="\n", maxn=1)
        # fix hyphen-ated words
        txt = preprocessing.normalize_hyphenated_words(txt)
        txt = preprocessing.normalize_quotation_marks(txt)
        txt = preprocessing.replace_urls(txt, replace_with="")
        txt = preprocessing.replace_phone_numbers(txt, replace_with="")
        txt = preprocessing.replace_emails(txt, replace_with="")
        txt = preprocessing.replace_user_handles(txt, replace_with="")
        txt = preprocessing.normalize_repeating_chars(txt, chars=".,;:-_ ", maxn=1)
        txt = re.sub("\n ", " ", txt)
        txt = re.sub(" \n", " ", txt)
        txt = re.sub("\n", " ", txt)
        txt = re.sub(" . ", " ", txt)

        # txt = text.encode().decode("unicode-escape")
        # Used ftfy for "fixing" broken text, e.g. Unicode
        # txt = fix_text(txt.strip(), normalization="NFKC")

        # re- minissence => reminissence
        # txt = re.sub(r"([a-z])\-\s{,2}([a-z])", r"\1\2", txt)

        # collapse two+ newlines into single whitespace
        # txt = re.sub(r"\s+\n{1,}\s*(\w)", r" \1", txt)

        # collapse two+ newlines into single whitespace
        # txt = re.sub("\n+", " ", txt)

        """
        # collapse two+ newlines into single whitespace
        txt = re.sub(r"\s+\n{2,}\s*(\w)", r" \1", txt)

        # double-newlines to dots
        txt = re.sub(r"\n\n", ". ", txt)

        # collapse whitespace
        txt = re.sub(r"(\s){2,}", r"\1", txt)
        # collapse dots
        txt = re.sub(r"\.{2,}", ".", txt)
        # newline to whitespace between word characters
        txt = re.sub(r"(\w)\n(\w)", r"\1 \2", txt)
        # newline + open brace to whitespace
        txt = re.sub(r"(\w)\n(\()", r"\1 \2", txt)
        # comma + newline  to whitespace
        txt = re.sub(r"(\w)\,\n(\w)", r"\1 \2", txt)

        # Number end of sentence, followed by sentence that starts with number + dot
        txt = re.sub(r"(\d+)\.(\d\.\s+)", r"\1. ", txt)
        # remove decimals + dot after whitespace followed by whitespace
        txt = re.sub(r"(\.\s*)\d+\.\s+", r"\1", txt)

        # collapse backslashes
        txt = re.sub(r"\\{2,}", r"\\", txt)
        # remove 'escaped backslash' artefacts
        txt = re.sub(r"\\\\", "", txt)
        # remove lowdash artifacts ("lines")
        txt = re.sub(r"_{2,}", r"", txt)

        # normalize newline
        txt = re.sub(r"\r\n", r"\n", txt)
        # Linebreaks starting with numbers \n77\n
        txt = re.sub(r"\n\d+\n", r"\n", txt)

        # remove quotes + decimals on beginning of sentences
        txt = re.sub(r"\.([\"']?)\d+\s+", r".\1", txt)
        # remove quotes + decimals on beginning of sentences
        txt = re.sub(r"\.([\"']?)\d+\s+", r".\1", txt)

        # collapse dots
        txt = re.sub(r"\.\s+\.", ". ", txt)
        # collapse whitespace
        txt = re.sub(r"(\w+)\s{2,}(\w+)", r"\1 \2", txt)

        # Add space+ dot with double quotes
        txt = re.sub(r"\.\"(\w+)", r'.". \1', txt)

        # Add space+ between two sentences
        txt = re.sub(r"([a-z])\.([A-Z])", r"\1. \2", txt)
        """

        return txt
