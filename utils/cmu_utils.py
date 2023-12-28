from pathlib import Path

def skip_line(line: str) -> bool:
    if line.startswith(';;;'):
        return True
    return False


def get_entry(line: str) -> list:
    word, phones = line.split(' ', 1)
    return word.strip(), phones.strip()


def cmu_parser(filepath: Path) -> dict:
    lexicon = {}

    with open(filepath, encoding='latin-1') as openfile:
        lines = openfile.readlines()
        for line in lines:
            if not skip_line(line):
                word, phones = get_entry(line)
                lexicon[word] = phones

    return lexicon