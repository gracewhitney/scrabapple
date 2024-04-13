import os

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


def validate_word(word, dictionary_name):
    if '-' in word:
        # TODO handle blanks
        return True
    if dictionary_name not in DAWGS:
        raise Exception(f"Unsupported dictionary {dictionary_name}")
    d = DAWGS[dictionary_name]
    return word.lower() in d
