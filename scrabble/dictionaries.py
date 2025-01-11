import os
import string

import dawg
from django.conf import settings

from scrabble.constants import Dictionary


def load_dawg(dictionary_name):
    d = dawg.CompletionDAWG()
    try:
        file_path = os.path.join(settings.BASE_DIR, f"dictionaries/{dictionary_name}.dawg")
        d.load(file_path)
    except Exception:
        raise Exception(f"Unsupported dictionary {dictionary_name}")
    return d


DAWGS = {
    dictionary: load_dawg(dictionary.value)
    for dictionary in Dictionary
}

BLANK_REPLACEMENT_MAPPING = {
    '-': [letter for letter in string.ascii_lowercase]
}
BLANK_REPLACEMENT = dawg.CompletionDAWG.compile_replaces(BLANK_REPLACEMENT_MAPPING)


def validate_word(word, dictionary_name):
    """Returns first matching word in dictionary"""
    if dictionary_name not in DAWGS:
        raise Exception(f"Unsupported dictionary {dictionary_name}")
    d = DAWGS[dictionary_name]
    matches = d.similar_keys(word.lower(), BLANK_REPLACEMENT)
    return matches[0] if matches else None
