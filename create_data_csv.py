import argparse
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
import csv
import logging
from typing import Generator
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
    is_short,
    random_reject,
    exclusively_contains_sil,
)


def load_dictionary() -> dict:
    lexicon = CMUDict()
    lexicon.load()
    lexicon.remove_heteronyms()
    return lexicon


def load_files(source_dir: Path) -> list:
    all_files = source_dir.glob('*of-00100')
    return all_files


def load_sentences(file_path: Path) -> Generator[str, None, None]:
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


def finalise_sentence(current_sentence: dict) -> dict:
    final_sentence = {}
    for key, value in current_sentence.items():
        if key != 'semiotic_classes':
            final_sentence[key] = value.strip()
        else:
            final_sentence[key] = value

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
        if skip_sentence(sentence):
            continue
        if not sproat_sentence_contains_oov(sentence, dictionary):
            final_sentences.append(sentence)

    return final_sentences


def skip_sentence(sentence: dict) -> bool:
    if exclusively_contains_sil(sentence):
        return True
    if is_short(sentence) and random_reject(0.9):
        return True
    if not normalisation_in_semiotic_classes(sentence['semiotic_classes']) and random_reject(0.5):
        return True
    return False


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


def save_to_csv(sentences: list, save_path: Path, writeheader=False) -> None:
    with open(save_path, 'a') as open_csv:
        fieldnames = ['original', 'normalised', 'phonemised']
        writer = csv.DictWriter(open_csv, fieldnames, extrasaction='ignore')

        if writeheader:
            writer.writeheader()
        for sentence in sentences:
            writer.writerow(sentence)

    logging.info(f'Saved CSV to {save_path}')



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", type=Path, help="The directory containing files to turn into a CSV", required=True)
    parser.add_argument("--target", type=Path, help="Where to save the CSV", required=True)
    args = parser.parse_args()

    dictionary = load_dictionary()
    files = load_files(args.source_dir)

    all_sentences = []
    for i, file in enumerate(files):
        sentences = load_sentences(file)
        sentences = subselect_sentences(sentences, dictionary)
        sentences = phonemise_sentences(sentences, dictionary)
        all_sentences += sentences

        if i == 0:
            save_to_csv(sentences, args.target, writeheader=True)
        else:
            save_to_csv(sentences, args.target)

        logging.info(f'Saved {len(sentences)} sentences from {file}, {len(all_sentences)} in total')

        if len(all_sentences) >= 50000:
            break

