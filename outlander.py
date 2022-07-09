import sys
import requests
import re
import json
from bs4 import BeautifulSoup

import spacy
import string
import os
from multiprocessing import Pool
from PyDictionary import PyDictionary
import argparse
import json

def lemmatize_text(text):
    sp = spacy.load('en_core_web_sm')  
    exclude = string.punctuation.replace("'", '')
    
    text = text.translate(str.maketrans('', '', exclude))
    lemmas = set()

    for word in sp(text):  
        lemmas.add(word.lemma_)
    return lemmas

def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)

# spotted at jonathanrjpereira/Ngram-Analytica
def ngrams(content, start, end, smoothing):
    url = "https://books.google.com/ngrams/json"

    querystring = {"content":content,
                   "case_insensitive":"on",
                   "year_start":start,
                   "year_end":end,
                   "corpus":"26",
                   "smoothing":smoothing}

    response = requests.get(url, params=querystring)
    data = response.json()

    graph = data[0]['timeseries']
    return graph

def meaning(word, threshold, dictionary):
    print(word)
    if mean(ngrams(word, 1950, 2019, 3)) < threshold:
        return dictionary.meaning(word)
    else:
        return None

def uncommon_word_definitions(words, threshold):
    dictionary=PyDictionary()
    available_cores = len(os.sched_getaffinity(0))

    with Pool(processes=available_cores) as pool:
        definitions = {word: pool.apply_async(meaning, args=(word, threshold, dictionary)).get() for word in words}
        filtered = {word: meaning for word, meaning in definitions.items() if meaning is not None}
        print(filtered)
        return filtered

def export(title, output_format, content):
    if output_format == 'anki':
        with open(title + '.txt', 'w') as outfile:
            outfile.write(json.dumps(content))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Map uncommon words in the text to their vocabulary definitions.")
    parser.add_argument('filename')
    args = parser.parse_args()
    
    with open(args.filename) as file:
        lemmas = lemmatize_text(file.read())
        lemmas = [x for x in lemmas if len(x.strip()) > 0]
        definitions = uncommon_word_definitions(lemmas, 1e-5)
        export(args.filename, 'anki', definitions)