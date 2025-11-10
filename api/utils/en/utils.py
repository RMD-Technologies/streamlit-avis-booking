import re
import string
from pathlib import Path
import json

    
def load_ngrams(file: str) -> list:
    bigram_path = Path(__file__).parent / file
    if not bigram_path.exists():
        raise FileNotFoundError(f"Missing bigram.tsv at: {bigram_path}")
    els = []
    with open(bigram_path, "r", encoding="utf-8") as f:
        for l in f.readlines():
            els.append(l.strip())
    return sorted(els, key=len, reverse=True)

def load_lemma_lookup() -> dict:
    """
    https://github.com/explosion/spacy-lookups-data/blob/1d90ebc5fdc6ccd0f9b2447e47172986938a7ab5/spacy_lookups_data/data/en_lemma_lookup.json
    """
    lemma_lookup_path = Path(__file__).parent / "en_lemma_lookup.json"
    if not lemma_lookup_path.exists():
        raise FileNotFoundError(f"Missing stopwords.txt at: {lemma_lookup_path}")
    with open(lemma_lookup_path, "r", encoding="utf-8") as f:
        d = json.load(f)
        d = {k.lower(): v.lower() for k, v in d.items()}
        d['bit'] = 'bit'
    return d

def load_stopwords() -> set:
    stopwords_path = Path(__file__).parent / "stopwords.txt"
    if not stopwords_path.exists():
        raise FileNotFoundError(f"Missing stopwords.txt at: {stopwords_path}")
    with open(stopwords_path, "r", encoding="utf-8") as f:
        return set(
            line.strip() for line in f
            if line.strip() and not line.startswith("#")
        )

LEMMA = load_lemma_lookup()
STOPWORDS = load_stopwords()
punctuations = string.punctuation + "…"
punctuations = punctuations.replace("&", "").replace("-", "").replace("/", "")
PUNCT_TABLE = str.maketrans('', '', punctuations)
STOPWORDS = STOPWORDS.union(punctuations)
NGRAMS = load_ngrams("trigram.txt") + load_ngrams("bigram.txt")

MIN_LEN_TOKEN = 2
MAX_LEN_TOKEN = 20

# --- Precompiled regex patterns ---

APOSTROPHE_VARIANTS = [
    "’",  # right single quotation mark
    "‘",  # left single quotation mark
    "‛",  # reversed single quotation mark
    "`",  # grave accent
    "´",  # acute accent
    "ʹ",  # modifier letter prime
    "ʻ",  # turned comma
    "ʽ",  # reversed comma
    "ʼ",  # modifier letter apostrophe
    "ʾ",  # right half ring
    "ʿ",  # left half ring
    '"',   # ASCII double quote
    "“",   # left double quotation mark
    "”",   # right double quotation mark
    "„",   # double low-9 quotation mark
    "‟",   # double high-reversed-9 quotation mark
    "″",   # double prime
    "❝",   # heavy double turned comma quotation mark ornament
    "❞",   # heavy double comma quotation mark ornament
    "«",   # left-pointing double angle quotation mark (guillemet)
    "»",   # right-pointing double angle quotation mark (guillemet)
    "‹",   # single left-pointing angle quotation mark
    "›",   # single right-pointing angle quotation mark
]

NT_EXCEPTIONS = {
    "can't": "can not",
    "won't": "will not",
    "shan't": "shall not",
    "ain't": "is not"
}


# Regex for general n't contractions
APOSTROPHE_PATTERN = re.compile("[" + re.escape("".join(APOSTROPHE_VARIANTS)) + "]")
NT_PATTERN = re.compile(r"\b(\w+)n[']t\b", flags=re.IGNORECASE)
DIGIT_PATTERN = re.compile(r"\d+")
DASH_PATTERN = re.compile(r"(?:(?<=\s)-+|-+(?=\s)|^-+|-+$)")  
SLASH_PATTERN = re.compile(
    r'\b(?![a-z]/[a-z]\b)(?!\d+[a-z]*\d*/\d+[a-z]*\d*\b)(\w+(?:/\w+)+)\b'
)

EMOJI_PATTERN = re.compile(
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


def custom_tokenize(text: str):
    """
    Tokenize text into words but keep tokens with
    '-' '/' '&' inside them intact.
    Example: B&B, 2024/2025, well-being.
    """
    # Pattern explanation:
    # [A-Za-z0-9]+   → start with alphanumeric
    # (?:[&/-][A-Za-z0-9]+)* → allow internal & / - followed by more alphanumerics
    pattern = re.compile(r"[A-Za-z0-9]+(?:[&/-][A-Za-z0-9]+)*")
    return pattern.findall(text)

def remove_emoji(text):
    # This regex matches most emojis, symbols, and pictographs
    return EMOJI_PATTERN.sub(r'', text)

def normalize_apostrophes(text: str) -> str:
    """
    Normalize apostrophe-like characters in text to the standard ASCII apostrophe (').
    """
    return APOSTROPHE_PATTERN.sub("'", text)

def replace_ng(match):
    return match.group(0).replace(" ", "_")

def normalize_dashes(text: str) -> str:
    """Remove standalone or edge dashes (but keep hyphenated words)."""
    return DASH_PATTERN.sub(" ", text)

def normalize_slashes(text: str) -> str:
    """
    Normalize slashes between words by adding spaces: 
    tea/coffee -> tea / coffee
    tea/milk/coffee -> tea / milk / coffee
    But keep numeric expressions like 24h/24 unchanged.
    """
    def replacer(match):
        return match.group(1).replace("/", " / ")
    return SLASH_PATTERN.sub(replacer, text)

def expand_nt_contractions(text: str) -> str:
    """
    Expand English n't contractions in text.
    Handles both regular forms (isn't -> is not)
    and irregular exceptions (can't -> can not).
    """
    # Handle exceptions first (case-insensitive)
    for contraction, expansion in NT_EXCEPTIONS.items():
        text = re.sub(
            rf"\b{re.escape(contraction)}\b", 
            expansion, 
            text, 
            flags=re.IGNORECASE
        )

    # Handle regular n't forms (e.g., doesn't -> does not)
    text = NT_PATTERN.sub(lambda m: m.group(1) + " not", text)

    return text

def lemmatize(text: str) -> str:
    """
    Lemmatize using the provided lemma dictionary.
    """
    tokens = custom_tokenize(text)
    lemmatized_tokens = [LEMMA.get(token, token) for token in tokens]
    return ' '.join(lemmatized_tokens).strip()

NGRAMS = [lemmatize(n) for n in NGRAMS]
NGRAM_PATTERN = re.compile(r'\b(?:' + '|'.join(map(re.escape, NGRAMS)) + r')\b')

def tokenize(sentence: str) -> list[str]:
    """
    Tokenize and normalize input sentence.
    """
    sentence = sentence.strip().lower()
    sentence = remove_emoji(sentence)
    sentence = normalize_apostrophes(sentence)
    sentence = normalize_slashes(sentence)
    sentence = normalize_dashes(sentence)
    sentence = expand_nt_contractions(sentence)
    sentence = lemmatize(sentence)
    sentence = sentence.translate(PUNCT_TABLE)
    sentence = NGRAM_PATTERN.sub(replace_ng, sentence)
    sentence = DIGIT_PATTERN.sub("NUM", sentence)
    
    tokens = [
        token
        for token in sentence.split()
        if MIN_LEN_TOKEN <= len(token) <= MAX_LEN_TOKEN
        and token not in STOPWORDS
    ]

    return tokens