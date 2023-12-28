from pathlib import Path
import re
import logging
from tqdm import tqdm
from abc import (
    ABC,
    abstractmethod,
)
from utils.cmu_utils import cmu_parser


class Lexicon(ABC):
    def init(self):
        self.dictionary = {}

    def lookup(self, word: str) -> str:
        try:
            return self.dictionary[word]
        except KeyError:
            return None
    
    @abstractmethod
    def load(self, file_path: Path):
        pass 

    @abstractmethod
    def remove_heteronyms(self):
        pass
  

class CMUDict(Lexicon):

    def load(self) -> dict:
        lexicon = cmu_parser('cmudict-0.7b')
        self.dictionary = lexicon

    def lookup(self, word: str) -> str:
        return super().lookup(word.upper())

    def remove_heteronyms(self):
        """Remove all the heteronyms. If a word has more than one possible pronuciation,
        we don't want it in the data at all."""
        logging.info(f'Removing heteronyms')
        keys = self.dictionary.copy().keys()
        for key in tqdm(keys):
            cleaned = re.sub(r"\(\d\)", '', key)
            if cleaned != key:
                del self.dictionary[key]
                try:
                    del self.dictionary[cleaned]
                except KeyError:
                    pass
                