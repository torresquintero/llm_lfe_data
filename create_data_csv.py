import argparse
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
import csv
import logging


def load_sentences(file_path: Path) -> list:
    sentences = []

    current_sentence = defaultdict(str)
    with open(file_path) as open_file:
        lines = open_file.readlines()
        for line in tqdm(lines):
            if contains_eos(line):
                final_sentence = finalise_sentence(current_sentence)
                sentences.append(final_sentence)
                current_sentence = defaultdict(str)
                continue

            current_sentence = update_current_sentence(line, current_sentence)
            
    return sentences


def contains_eos(line: str) -> bool:
    return '<eos>' in line


def finalise_sentence(current_sentence: dict) -> dict:
    final_sentence = {}
    for key, value in current_sentence.items():
        final_sentence[key] = value.strip()

    return final_sentence


def update_current_sentence(line: str, current_sentence: dict) -> dict:
    original_token = get_original_token(line)
    normalised_token = get_normalised_token(line)

    current_sentence['original'] += f'{original_token} '
    current_sentence['normalised'] += f'{normalised_token} '

    return current_sentence



def get_original_token(line: str) -> str:
    _, original_token, _ = line.strip().split('\t')
    return original_token


def get_normalised_token(line: str) -> str:
    _, original_token, normalised_token = line.strip().split('\t')
    normalised_token = original_token if no_normalisation(normalised_token) else normalised_token
    normalised_token = clean_sil(normalised_token)
    return normalised_token


def no_normalisation(normalised_token: str) -> bool:
    return normalised_token == '<self>'


def clean_sil(normalised_token: str) -> str:
    if normalised_token == 'sil':
        return '<sil>'
    return normalised_token


def save_to_csv(sentences: list, save_path: Path) -> None:
    with open(save_path, 'w') as open_csv:
        fieldnames = ['original', 'normalised']
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


    sentences = load_sentences(args.source)
    save_to_csv(sentences, args.target)

