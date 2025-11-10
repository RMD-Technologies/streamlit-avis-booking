from .fr.utils import preprocess_text_for_word2vec as fr_tokenize
from .en.utils import tokenize as en_tokenize

def batch_tokenize(batch: list):
    outputs = []
    for lang, text in batch:
        try:
            outputs.append({"tokens": tokenize(lang, text)})
        except Exception as e:
            outputs.append({"Error": str(e)})
    return outputs

def tokenize(lang: str, text: str):
    if lang == 'fr':
        return fr_tokenize(text)
    elif lang == 'en':
        return en_tokenize(text)
    else:
        raise ValueError(f"Unsupported language: {lang}. Supported languages are 'fr' and 'en'.")
