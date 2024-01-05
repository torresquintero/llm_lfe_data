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


    def manually_modify_and_remove_entires(self):
        """Manual corrections and modifications that Ale can make as a linguist"""
        self.dictionary['THE_VOWEL'] = 'DH IY0'
        self.dictionary['THE_CONSONANT'] = 'DH AH0'

        # For the word "in" there are two entries: one stressed and one not stressed.
        # As this is a functional word most of the time, let's just get rid of the stressed option all together
        del self.dictionary['IN(1)']

        # For the word "with" there are four entries. Two end in a voiced consonant and the other in a voiceless consonant.
        # And each has a stressed and non stressed version. In my dialect it's hard to imagine this word ending voiced, and as
        # another function word, we should default to the non-stressed version
        self.dictionary['WITH'] = self.dictionary['WITH(2)']
        del self.dictionary['WITH(1)']
        del self.dictionary['WITH(2)']
        del self.dictionary['WITH(3)']

        # CMU has a version of "which" that starts with a voiceless cononant. IMO as a native speaker this version of the
        # word is pretty archaic and not really used anymore
        del self.dictionary['WHICH(1)']

        # same thing with "while"
        del self.dictionary['WHILE(1)']

        # same thing with "one"
        del self.dictionary['ONE(1)']

        # "Are" is rarely stressed. For our LLM-LFE usecase, okay to always use non-stressed
        self.dictionary['ARE'] = self.dictionary['ARE(1)']
        del self.dictionary['ARE(1)']

        # Similarly for is rarely stresed in connected speech, and idk what's going with FOR(2)
        self.dictionary['FOR'] = self.dictionary['FOR(1)']
        del self.dictionary['FOR(1)']
        del self.dictionary['FOR(2)']

        # remove non-schwa version of relief in first syllable
        del self.dictionary['RELIEF(1)']

        # remove secondary stress of first syllable version of "before"
        del self.dictionary['BEFORE(1)']

        # remove stressed version of "of"
        self.dictionary['OF'] = self.dictionary['OF(1)']
        del self.dictionary['OF(1)']

        # remove non-stressed version of "be". Given the vowel quality, should this word always carry stress?
        del self.dictionary['BE(1)']

        # second pron of "as" seems weird to me
        del self.dictionary['AS(1)']

        # remove stressed version of "and"
        del self.dictionary['AND(1)']

        # remove stressed version of "it"
        self.dictionary['IT'] = self.dictionary['IT(1)']
        del self.dictionary['IT(1)']

        # remove stressed version of "is"
        self.dictionary['IS'] = self.dictionary['IS(1)']
        del self.dictionary['IS(1)']

        # remove stressed version of "or"
        self.dictionary['OR'] = self.dictionary['OR(1)']
        del self.dictionary['OR(1)']

        # remove stressed version of "has"
        self.dictionary['HAS'] = self.dictionary['HAS(1)']
        del self.dictionary['HAS(1)']

        # "been" has three prons: one with schwa, and two with IH stressed and unstressed. IMO IH non-stressed is
        # the most common
        self.dictionary['BEEN'] = self.dictionary['BEEN(2)']
        del self.dictionary['BEEN(1)']
        del self.dictionary['BEEN(2)']

        # remove stressed version of than
        self.dictionary['THAN'] = self.dictionary['THAN(1)']
        del self.dictionary['THAN(1)']

        # remove stressed version of was
        self.dictionary['WAS'] = self.dictionary['WAS(1)']
        del self.dictionary['WAS(1)']

        # "to" has three prons, one stressed, and two non-stressed with IH and AH. IMO the non-stressed AH version is
        # most common
        self.dictionary['TO'] = self.dictionary['TO(2)']
        del self.dictionary['TO(1)']
        del self.dictionary['TO(2)']

        # two versions of "on" with AA and AO. IMO AA is more common unless you're like from New York
        del self.dictionary['ON(1)']

        # two versions of "an". Get rid of the stressed version
        self.dictionary['AN'] = self.dictionary['AN(1)']
        del self.dictionary['AN(1)']

        # remove stressed version of "this"
        self.dictionary['THIS'] = self.dictionary['THIS(1)']
        del self.dictionary['THIS(1)']

        # version of most without final t feels kinda allophonic to me? In my speech I think I always close my toung
        # even if I don't release. So let's get rid of the version without final t
        del self.dictionary['MOST(1)']

        # same thing with final t in "next"
        del self.dictionary['NEXT(1)']

        # two versions of "rather" with AE and  AH. I think AE is more accurate
        del self.dictionary['RATHER(1)']

        # two versions of "ended" wtth AH and IH. I think IH is more accurate
        self.dictionary['ENDED'] = self.dictionary['ENDED(1)']
        del self.dictionary['ENDED(1)']



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
