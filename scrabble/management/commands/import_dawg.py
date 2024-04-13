import os.path

import dawg
from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--input', required=True)
        parser.add_argument('--name', required=True)

    def handle(self, *args, **options):
        """
        Creates a DAWG file from a wordlist with the given name.
        Assumes valid words are line separated, strips extra words on each line.
        """
        file_path = options["input"]
        dictionary_name = options["name"]
        with open(file_path, 'r') as f:
            words = [
                line.split(" ")[0].strip().lower()
                for line in f.readlines()
            ]
        d = dawg.CompletionDAWG(words)
        dawg_file_name = os.path.join(settings.BASE_DIR, f"dictionaries/{dictionary_name}.dawg")
        d.save(dawg_file_name)
