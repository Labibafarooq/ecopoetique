import re

"""
Cette classe identifie les phrases dans un texte en français et renvoie une liste de ces phrases.
Appel de la classe : Sentencizer(texte_a_tokeniser).sentences

"""


class Sentencizer:

    def __init__(self, input_text, split_regex=[r'\.{1,}', r'…', r'[!\?]+'], delimiter_token='<SPLIT>'):
        self.sentences = []
        self.raw = str(input_text)
        self._split_regex = split_regex
        self._delimiter_token = delimiter_token
        self._index=0
        self._sentencize()

    def _sentencize(self):
        text = self.raw
        
        # Escape acronyms or abbreviations
        regex_abbr = re.compile(r"\b(?:[a-zA-Z]\.|M\.|Dr\.|Mme\.){1,}")
        abbr_list = re.findall(regex_abbr, text)
        
        for i, abbr in enumerate(abbr_list):
            text = text.replace(abbr, '<ABBR'+str(i)+'>')
        
        # Special case
        regex_spec = re.compile(r'[\!\?\.] »')
        spec_list = re.findall(regex_spec, text)
        
        for i, spec in enumerate(spec_list):
            text = text.replace(spec, '<SPEC'+str(i)+'>')
        
        
        for regex in self._split_regex:
            text = re.sub(regex, lambda x:x.group(0)+""+self._delimiter_token, text)
            print(text)
        
        # Restore acronyms
        text = re.sub(r"<ABBR([0-9]+)>", lambda x: abbr_list[int(x.group(1))], text)
        
        # Restore spec
        text = re.sub(r"<SPEC([0-9]+)>", lambda x: spec_list[int(x.group(1))], text)
        text = re.sub(regex_spec, lambda x:x.group(0)+""+self._delimiter_token, text)
        
        # Split text
        self.sentences = [x.strip() for x in text.split(self._delimiter_token) if x != '' ]

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < len(self.sentences):
            result = self.sentences[self._index]
            self._index+=1
            return result
        raise StopIteration
