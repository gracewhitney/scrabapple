import os
import string

import dawg
from django.conf import settings

from scrabble.constants import Dictionary, BLANK_CHARS


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


def validate_word(word, dictionary_names, blank_replacements):
    """
    Checks whether matching word exists in dictionary.
    Side effect: Also updates blank_replacements by reference.
    """
    # Empty replacement list errors -- remove from dict
    filtered_replacements = {char: value for char, value in blank_replacements.items() if value}
    replaces = dawg.CompletionDAWG.compile_replaces(filtered_replacements)
    matches = set()
    for dictionary_name in dictionary_names:
        if dictionary_name not in DAWGS:
            raise Exception(f"Unsupported dictionary {dictionary_name}")
        d = DAWGS[dictionary_name]
        matches.update(d.similar_keys(word.lower(), replaces))
    for char in BLANK_CHARS:
        if char in word:
            i = word.index(char)
            char_matches = [match[i] for match in matches]
            # Update replacement lists in place (passed by reference)
            blank_replacements[char] = char_matches
    return bool(matches)
