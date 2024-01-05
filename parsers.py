from abc import (
    abstractmethod,
    ABC,
)
import logging
from pathlib import Path
from tqdm import tqdm


from lexicon import Lexicon
from utils.utils import (
    contains_eos,
    is_sil,
    contains_oov,
    strip_sentence,
    replace_punct_with_sil,
    modify_word_for_lex_lookup,
    remove_extra_spaces,
)
from utils.sproat_utils import (
    update_sentence,
    skip_sentence,
)


def phonemise_sentence(sentence: str, dictionary: Lexicon) -> str:
    phonemised_sentence = '<w> '
    tokens = sentence.split()
    for i, token in enumerate(tokens):
        if not is_sil(token):
            token = modify_word_for_lex_lookup(token, tokens, i)
            phones = dictionary.lookup(token) + ' <w> '
        # avoid repeated <sil> in phonemisation
        elif not phonemised_sentence.endswith('<sil> <w> '):
            phones = '<sil> <w> '
        else:
            phones = ''
        phonemised_sentence += phones

    return phonemised_sentence.strip()


class Parser(ABC):

    def __init__(self):
        self.sentences = []

    def parse_file(self):
        logging.info('Loading sentences')

    def clean_sentences(self):
        logging.info('Cleaning sentences')

    def subselect_sentences(self):
        logging.info('Subselecting sentences')

    def phonemise_sentences(self, dictionary: Lexicon):
        logging.info('Phonemising sentences')
        for sentence in tqdm(self.sentences):
            sentence['phonemised'] = phonemise_sentence(sentence['normalised'], dictionary)


class SproatParser(Parser):

    def parse_file(self, filepath: Path):
        super().parse_file()

        current_sentence = {
            'original': '',
            'normalised': '',
            'semiotic_classes': set(),
        }
        with open(filepath) as open_file:
            lines = open_file.readlines()
            for line in tqdm(lines):
                if contains_eos(line):
                    self.sentences.append(current_sentence)
                    current_sentence = {
                        'original': '',
                        'normalised': '',
                        'semiotic_classes': set(),
                    }
                    continue

                current_sentence = update_sentence(line, current_sentence)

    def clean_sentences(self):
        super().clean_sentences()
        final_sentences = []

        for sentence in tqdm(self.sentences):
            sentence = strip_sentence(sentence)

        self.sentences = final_sentences

    def subselect_sentences(self, dictionary: Lexicon):
        super().subselect_sentences()

        final_sentences = []
        for sentence in tqdm(self.sentences):
            if skip_sentence(sentence):
                continue
            if not contains_oov(sentence['normalised'], dictionary):
                final_sentences.append(sentence)

        self.sentences = final_sentences


class LJParser(Parser):

    def parse_file(self, filepath: Path):
        super().parse_file()

        with open(filepath) as open_file:
            lines = open_file.readlines()
            for line in lines:
                _, original, normalised = line.split('|')
                sentence = {
                    'original': original,
                    'normalised': normalised,
                }
                sentence = strip_sentence(sentence)
                sentence = replace_punct_with_sil(sentence)
                self.sentences.append(sentence)

    def clean_sentences(self):
        super().clean_sentences()
        final_sentences = []

        for sentence in tqdm(self.sentences):
            sentence = strip_sentence(sentence)
            sentence = replace_punct_with_sil(sentence)
            sentence = remove_extra_spaces(sentence)

        self.sentences = final_sentences

    def subselect_sentences(self, dictionary: Lexicon):
        super().subselect_sentences()

        final_sentences = []
        for sentence in tqdm(self.sentences):
            if not contains_oov(sentence['normalised'], dictionary):
                final_sentences.append(sentence)

        self.sentences = final_sentences
