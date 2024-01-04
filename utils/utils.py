from lexicon import Lexicon
from random import random


def contains_eos(string: str) -> bool:
    return '<eos>' in string


def token_not_normalised(normalised_token: str) -> bool:
    return normalised_token == '<self>'


def normalisation_in_semiotic_classes(semiotic_classes: set) -> bool:
    if semiotic_classes == {'PLAIN', 'PUNCT'}:
         return False
    if semiotic_classes == {'PLAIN'}:
        return False
    if semiotic_classes == {'PUNCT'}:
        return False
    return True


def is_short(sentence: dict) -> bool:
    return len(sentence['original'].split(' ')) < 15


def clean_sil(normalised_token: str) -> str:
    if normalised_token == 'sil':
        return '<sil>'
    return normalised_token


def remove_sil(string: str) -> str:
    return string.replace('<sil>', '')


def is_sil(string: str) -> bool:
    return string == '<sil>'


def exclusively_contains_sil(sentence: dict) -> bool:
    return all(is_sil(token) for token in sentence['normalised'].strip().split(' '))


def contains_oov(sentence: str, dictionary: Lexicon) -> bool:
    words = sentence.split()
    for word in words:
        if not dictionary.lookup(word):
            return True
    return False

def random_reject(probability: float) -> bool:
    # randomly reject a sentence given a probabilty
    return random() < probability
