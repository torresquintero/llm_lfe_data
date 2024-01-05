from lexicon import Lexicon

from utils.utils import (
    exclusively_contains_sil,
    is_short,
    random_reject,
)

def token_not_normalised(normalised_token: str) -> bool:
    return normalised_token == '<self>'


def clean_sil(normalised_token: str) -> str:
    if normalised_token == 'sil':
        return '<sil>'
    return normalised_token


def get_semiotic_class(line: str) -> str:
    semiotic_class, _, _ = line.strip().split('\t')
    return semiotic_class


def get_original_token(line: str) -> str:
    _, original_token, _ = line.strip().split('\t')
    return original_token


def get_normalised_token(line: str) -> str:
    _, original_token, normalised_token = line.strip().split('\t')
    normalised_token = original_token if token_not_normalised(normalised_token) else normalised_token
    normalised_token = clean_sil(normalised_token)
    return normalised_token


def update_sentence(line: str, current_sentence: dict) -> dict:
    semiotic_class = get_semiotic_class(line)
    original_token = get_original_token(line)
    normalised_token = get_normalised_token(line)

    current_sentence['semiotic_classes'].add(semiotic_class)
    current_sentence['original'] += f'{original_token} '
    current_sentence['normalised'] += f'{normalised_token} '

    return current_sentence


def skip_sentence(sentence: dict) -> bool:
    if exclusively_contains_sil(sentence):
        return True
    if is_short(sentence) and random_reject(0.9):
        return True
    if not normalisation_in_semiotic_classes(sentence['semiotic_classes']) and random_reject(0.5):
        return True
    return False


def normalisation_in_semiotic_classes(semiotic_classes: set) -> bool:
    if semiotic_classes == {'PLAIN', 'PUNCT'}:
         return False
    if semiotic_classes == {'PLAIN'}:
        return False
    if semiotic_classes == {'PUNCT'}:
        return False
    return True
