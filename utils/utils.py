from lexicon import Lexicon
from random import random
import re

VOWELS = ('a', 'e', 'i', 'o', 'u')


def contains_eos(string: str) -> bool:
    return '<eos>' in string


def is_short(sentence: dict) -> bool:
    return len(sentence['original'].split(' ')) < 15


def remove_sil(string: str) -> str:
    return string.replace('<sil>', '')


def is_sil(string: str) -> bool:
    return string == '<sil>'


def exclusively_contains_sil(sentence: dict) -> bool:
    return all(is_sil(token) for token in sentence['normalised'].strip().split(' '))


def contains_oov(sentence: str, dictionary: Lexicon) -> bool:
    sentence = remove_sil(sentence)
    words = sentence.split()
    for i, word in enumerate(words):
        word = modify_word_for_lex_lookup(word, words, i)

        if not dictionary.lookup(word):
            return True
    return False


def modify_word_for_lex_lookup(word: str, words: list, i: int) -> str:
    if len(words) == i + 1:
        return word
    if word.lower() == 'the' and words[i + 1].startswith(VOWELS):
        return 'THE_VOWEL'
    if word.lower() == 'the' and not words[i + 1].startswith(VOWELS):
        return 'THE_CONSONANT'
    return word


def random_reject(probability: float) -> bool:
    # randomly reject a sentence given a probabilty
    return random() < probability


def strip_sentence(sentence: dict) -> dict:
    final_sentence = {}
    for key, value in sentence.items():
        if type(value) == str:
            final_sentence[key] = value.strip()
        else:
            final_sentence[key] = value

    return final_sentence


def replace_punct_with_sil(sentence: dict) -> dict:
    # following sproat et al, all 'normalised' sentences should have punctuation replaced with sil
    normalised = sentence['normalised']

    normalised = normalised.replace(',', ' <sil> ')
    normalised = normalised.replace(';', ' <sil> ')
    normalised = normalised.replace('"', ' <sil> ')
    normalised = f'{normalised[:-1]} <sil>' if normalised.endswith('.') else normalised
    normalised = f'{normalised[:-1]} <sil>' if normalised.endswith(',') else normalised
    normalised = f'{normalised[:-1]} <sil>' if normalised.endswith(';') else normalised

    sentence['normalised'] = normalised

    return sentence

def remove_extra_spaces(sentence: dict) -> dict:
    sentence['normalised'] = re.sub(' +', ' ', sentence['normalised'])
    return sentence
