import argparse
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
import csv
import logging
from lexicon import (
    CMUDict,
    Lexicon,
)
from utils.utils import (
    contains_eos,
    token_not_normalised,
    clean_sil,
    contains_oov,
    remove_sil,
    normalisation_in_semiotic_classes,
    is_sil,
)


def load_dictionary() -> dict:
    lexicon = CMUDict()
    lexicon.load()
    lexicon.remove_heteronyms()
    return lexicon


def load_sentences(file_path: Path) -> list:
    logging.info(f'Loading sentences')
    sentences = []

    current_sentence = {
        'original': '',
        'normalised': '',
        'semiotic_classes': set(),
    }
    with open(file_path) as open_file:
        lines = open_file.readlines()
        for line in tqdm(lines):
            if contains_eos(line):
                if not skip_sentence(current_sentence):
                    final_sentence = finalise_sentence(current_sentence)
                    sentences.append(final_sentence)
                current_sentence = {
                    'original': '',
                    'normalised': '',
                    'semiotic_classes': set(),
                }
                continue

            current_sentence = update_current_sentence(line, current_sentence)
            
    return sentences


def skip_sentence(current_sentence: dict) -> bool:
    return not normalisation_in_semiotic_classes(current_sentence['semiotic_classes'])


def finalise_sentence(current_sentence: dict) -> dict:
    final_sentence = {}
    for key, value in current_sentence.items():
        if key != 'semiotic_classes':
            final_sentence[key] = value.strip()

    return final_sentence


def update_current_sentence(line: str, current_sentence: dict) -> dict:
    semiotic_class = get_semiotic_class(line)
    original_token = get_original_token(line)
    normalised_token = get_normalised_token(line)

    current_sentence['semiotic_classes'].add(semiotic_class)
    current_sentence['original'] += f'{original_token} '
    current_sentence['normalised'] += f'{normalised_token} '

    return current_sentence


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


def subselect_sentences(sentences: list, dictionary: Lexicon) -> list:
    logging.info(f'Subselecting sentences')
    final_sentences = []
    for sentence in tqdm(sentences):
        if not sproat_sentence_contains_oov(sentence, dictionary):
            final_sentences.append(sentence)
    
    return final_sentences


def sproat_sentence_contains_oov(sentence: dict, dictionary: Lexicon) -> bool:
    normalised = sentence['normalised']
    normalised = remove_sil(normalised)

    return contains_oov(normalised, dictionary)


def phonemise_sentences(sentences: list, dictionary: Lexicon) -> list:
    logging.info(f'Phonemising sentences')
    for sentence in tqdm(sentences):
        sentence['phonemised'] = phonemise_sentence(sentence['normalised'], dictionary)
    return sentences


def phonemise_sentence(sentence: str, dictionary: Lexicon) -> str:
    phonemised_sentence = '<w> '
    tokens = sentence.split()
    for token in tokens:
        if not is_sil(token):
            phones = dictionary.lookup(token) + ' <w> '
        # avoid repeated <sil> in phonemisation
        elif not phonemised_sentence.endswith('<sil> <w> '):
            phones = '<sil> <w> '
        else:
            phones = ''
        phonemised_sentence += phones

    return phonemised_sentence.strip()


def save_to_csv(sentences: list, save_path: Path) -> None:
    with open(save_path, 'w') as open_csv:
        fieldnames = ['original', 'normalised', 'phonemised']
        writer = csv.DictWriter(open_csv, fieldnames)

        writer.writeheader()
        for sentence in sentences:
            writer.writerow(sentence)

    logging.info(f'Saved CSV to {save_path}')



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, help="The file to turn into a CSV", required=True)
    parser.add_argument("--target", type=Path, help="Where to save the CSV", required=True)
    args = parser.parse_args()

    dictionary = load_dictionary()
    sentences = load_sentences(args.source)
    sentences = subselect_sentences(sentences, dictionary)
    sentences = phonemise_sentences(sentences, dictionary)

    save_to_csv(sentences, args.target)

