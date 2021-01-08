import app
from os import path
import logging
import re
import pkg_resources
from symspellpy import SymSpell, Verbosity

import string


log = logging.getLogger(__name__)


class Spellchecker(object):
    """
    We use https://github.com/mammothb/symspellpy to do basic word / n-gram based spell checking.
    It is based on SymSpell:
    https://github.com/wolfgarbe/SymSpell

    TODO: We should be very cautious here and only "auto-correct" small one-off OCR errors (like "mnlicious -> malicious"),
    as otherwise we may change domain specific terms and abbreviations.

    TODO: consider optionally using a OCR cloud API,
    like: https://www.abbyy.com/cloud-ocr-sdk/
    https://cloud.ocrsdk.com/demo/

    This gives (much) better results, but it ain't free ;-)



    """

    sym_spell = None
    dictionary_path = None
    max_edit_distance = 1
    max_dict_edit_distance = 2
    prefix_length = 7
    count_threshold = 2

    def __init__(self, language="en"):
        self.sym_spell = SymSpell(
            max_dictionary_edit_distance=self.max_dict_edit_distance,
            prefix_length=self.prefix_length,
            count_threshold=self.count_threshold,
        )
        # FIXME support non-english languages and custom models
        if language == "en":
            self.dictionary_path = pkg_resources.resource_filename(
                "symspellpy", "frequency_dictionary_en_82_765.txt"
            )
            # term_index is the column of the term and count_index is the
            # column of the term frequency
            self.sym_spell.load_dictionary(
                self.dictionary_path, term_index=0, count_index=1
            )
        else:
            log.warning(f"No spell checking available for language '{language}'")
            self.sym_spell = None

    def suggestions(self, input_term):
        # No suggestions if no spell checker available
        if not self.sym_spell:
            return []

        # max edit distance per lookup
        # (max_edit_distance_lookup <= max_dictionary_edit_distance)
        suggestions = self.sym_spell.lookup(
            input_term,
            Verbosity.CLOSEST,
            max_edit_distance=self.max_edit_distance,
            include_unknown=False,
            transfer_casing=True,
        )
        return suggestions

    def correct_word(self, input_term):
        stripped = str(input_term).strip(string.punctuation)

        # Don't correct words shorter than 4 chars (too risky it might be a domain specific abbreviation )
        if len(stripped) < 4:
            return input_term

        # if less alpha chars than alpha chars: ignore
        if len(re.findall(r"[A-Za-z]", stripped)) <= len(
            re.findall(r"[^A-Za-z]", stripped)
        ):
            return input_term

        suggestions = self.suggestions(stripped)

        # No suggestions? Leave it as is
        if len(suggestions) == 0:
            return input_term

        # OCR tokenizer may leave training punctation -> re-add
        candidate = suggestions[0].term
        for i in [-2, -1]:
            if input_term[i] in string.punctuation:
                candidate += input_term[i]

        return candidate
