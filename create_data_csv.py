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
from parsers import (
    LJParser,
    SproatParser,
)


def load_dictionary() -> dict:
    lexicon = CMUDict()
    lexicon.load()
    lexicon.manually_modify_and_remove_entires()
    lexicon.remove_heteronyms()
    return lexicon


def load_lj_sentences(dictionary: dict) -> list:
    lj = LJParser()
    lj.parse_file(Path('data/LJSpeech-1.1/metadata.csv'))
    lj.subselect_sentences(dictionary)
    lj.phonemise_sentences(dictionary)
    return lj.sentences


def load_files(source_dir: Path) -> list:
    all_files = source_dir.glob('*of-00100')
    return all_files


def save_to_csv(sentences: list, save_path: Path, lj_sentences: list, writeheader=False) -> None:
    with open(save_path, 'a') as open_csv:
        fieldnames = ['original', 'normalised', 'phonemised']
        writer = csv.DictWriter(open_csv, fieldnames, extrasaction='ignore')

        if writeheader:
            writer.writeheader()
        for i, sentence in enumerate(sentences):
            # we have ~1000 lj sentences and want ~20k sentences. So every 20th sentence should be an LJ sentence
            if i % 20 == 0 and lj_sentences:
                lj_sentence = lj_sentences[0]
                writer.writerow(lj_sentence)
                lj_sentences.remove(lj_sentence)


            writer.writerow(sentence)

    logging.info(f'Saved CSV to {save_path}')



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", type=Path, help="The directory containing files to turn into a CSV", required=True)
    parser.add_argument("--target", type=Path, help="Where to save the CSV", required=True)
    args = parser.parse_args()

    dictionary = load_dictionary()
    lj_sentences = load_lj_sentences(dictionary)

    sproat_files = load_files(args.source_dir)

    all_sentences = []
    for i, file in enumerate(sproat_files):
        parser = SproatParser()
        parser.parse_file(file)
        parser.subselect_sentences(dictionary)
        parser.phonemise_sentences(dictionary)
        sentences = parser.sentences

        all_sentences += sentences

        if i == 0:
            save_to_csv(sentences, args.target, lj_sentences, writeheader=True, )
        else:
            save_to_csv(sentences, args.target, lj_sentences)

        total_lines = sum(1 for _ in open(args.target))
        logging.info(f'Saved {len(sentences)} sentences from {file}, {total_lines} in total')

        if len(all_sentences) >= 20000:
            break

