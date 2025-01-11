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

BLANK_REPLACEMENT_MAPPING = {
    char: [letter for letter in string.ascii_lowercase]
    for char in BLANK_CHARS
}
BLANK_REPLACEMENT = dawg.CompletionDAWG.compile_replaces(BLANK_REPLACEMENT_MAPPING)


def validate_word(word, dictionary_names, blank_replacements):
    """Checks whether matching word exists in dictionary. Also updates blank_replacements by reference."""
    replaces = dawg.CompletionDAWG.compile_replaces(blank_replacements) if blank_replacements else BLANK_REPLACEMENT
    matches = set()
    for dictionary_name in dictionary_names:
        if dictionary_name not in DAWGS:
            raise Exception(f"Unsupported dictionary {dictionary_name}")
        d = DAWGS[dictionary_name]
        matches.update(d.similar_keys(word.lower(), replaces))
    if matches:
        for char in BLANK_CHARS:
            if char in word:
                i = word.index(char)
                char_matches = [match[i] for match in matches]
                blank_replacements[char] = char_matches
    return bool(matches)
