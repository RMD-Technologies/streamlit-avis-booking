import re
import string
import nltk
from typing import List
from nltk.tokenize import sent_tokenize, word_tokenize
import unicodedata
from .special_token import fixed_ngrams, pattern_rules, abbrevation
from pathlib import Path
import json

# Download sentence tokenizer if needed
nltk.download('punkt', quiet=True)



# Load custom stopwords from stopwords.txt (same directory as this script)

def load_custom_stopwords() -> set:
    stopwords_path = Path(__file__).parent / "stopwords.txt"
    if not stopwords_path.exists():
        raise FileNotFoundError(f"Missing stopwords.txt at: {stopwords_path}")
    with open(stopwords_path, "r", encoding="utf-8") as f:
        return set(
            line.strip() for line in f
            if line.strip() and not line.startswith("#")
        )

def load_fr_lemma_lookup() -> dict:
    """
    https://github.com/explosion/spacy-lookups-data/blob/1d90ebc5fdc6ccd0f9b2447e47172986938a7ab5/spacy_lookups_data/data/fr_lemma_lookup.json"
    """
    fr_lemma_lookup_path = Path(__file__).parent / "fr_lemma_lookup.json"
    if not fr_lemma_lookup_path.exists():
        raise FileNotFoundError(f"Missing stopwords.txt at: {fr_lemma_lookup_path}")
    with open(fr_lemma_lookup_path, "r", encoding="utf-8") as f:
        d = json.load(f)
        dd = dict()
        for key, values in d.items():
            v = values[0]
            if v == 'situé':
                v = 'situer'
            dd[key] = v
        dd['minutes'] = 'minute'
        dd['affaires'] = 'affaire'
        dd['étoiles'] = 'étoile'
        dd['moquettes'] = 'moquette'
        del dd['cheveux']
        for key, value in abbrevation.items():
            dd[key] = value
        return dd

# Load once at top level
STOPWORDS = load_custom_stopwords()
D_FR_LEMMA = load_fr_lemma_lookup()
punctuations = string.punctuation + "…" + "¨" + "“" + "”" + "’" + "´"
punctuations = punctuations.replace("'", '')
STOPWORDS = STOPWORDS.union(punctuations)
punct_table = str.maketrans({p: ' ' for p in punctuations})


def normalize_apostrophes(text: str) -> str:
    text = text.replace("’", "'").replace("´", "'")
    text = text.replace("'", "' ")
    return text


def remove_emoji(text):
    # This regex matches most emojis, symbols, and pictographs
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002500-\U00002BEF"  # chinese characters (common in emoji art)
        "\U00002702-\U000027B0"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # dingbats
        "\u3030"
        "]+", flags=re.UNICODE)
    
    return emoji_pattern.sub(r'', text)

def normalize_phrases_and_patterns(text: str) -> str:
    
    for key, values in fixed_ngrams.items():
        for phrase in sorted(values, key=lambda x: -len(x)):
            pattern = r"\b" + re.escape(phrase) + r"(s)?\b"
            replacement = phrase.replace(" ", key)
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    for pattern, replacement in pattern_rules:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


def lemmatize_sentence(sentence: str) -> str:
    """
    Lemmatize a French sentence using the provided lemma dictionary.
    """
    tokens = sentence.split()
    lemmatized_tokens = [D_FR_LEMMA.get(token, token) for token in tokens]
    return ' '.join(lemmatized_tokens).strip()

def french_sent_tokenize(text: str):
    return sent_tokenize(text, language='french')

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def preprocess_text_for_word2vec(
    sentence: str,
    min_token_len: int = 2,
    max_token_len: int = 20
) -> List[str]:
    """
    Full preprocessing pipeline (reordered):
    1. Remove emoji
    2. Lemmatize tokens
    3. Normalize phrases and patterns
    4. Remove stopwords
    5. Tokenize
    """

    # Lowercase first for consistency
    sentence = sentence.lower()

    sentence = sentence.replace("œ", "oe")

    # 1. Remove emoji
    sentence = remove_emoji(sentence)

    # Optional: normalize apostrophes before lemmatization
    sentence = normalize_apostrophes(sentence)

    # Remove punctuation (optional before lemmatization)
    sentence = sentence.translate(punct_table)

    # 2. Lemmatize tokens (assumes you have a lemmatize_sentence function)
    sentence = lemmatize_sentence(sentence)

    sentence = sentence.replace("'", '')

    # 3. Normalize phrases and patterns
    sentence = normalize_phrases_and_patterns(sentence)

    # Replace digits with placeholder
    sentence = re.sub(r"\d+", "NUM", sentence)

    # 4. Tokenize
    tokens = sentence.split()

    # 5. Remove stopwords + length filter
    tokens = [
        strip_accents(token) for token in tokens
        if token not in STOPWORDS
        and min_token_len <= len(token) <= max_token_len
    ]


    return tokens