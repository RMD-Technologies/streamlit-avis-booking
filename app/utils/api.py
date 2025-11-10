import os
import requests


TOKENIZE_API_ULR = os.getenv("TOKENIZE_API_URL")
WORD_EMBEDIDNGS_API_URL = os.getenv("WORD_EMBEDDINGS_API_URL")
SENTENCE_EMBEDDINGS_API_URL = os.getenv("SENTENCE_EMBEDDINGS_API_URL")

def tokenize(reviews, lang="fr") -> list[str]:

    payload = {"input": []}

    keys = []
    for r in reviews:
        if lang != r['language_text']: continue
        for key in ['review_title', 'positive_text', 'negative_text']:
            if not r[key]: continue
            payload['input'].append({
                "lang": lang,
                "text": r[key]
            })
            keys.append(key)

    response = requests.post(TOKENIZE_API_ULR, json=payload)
    response.raise_for_status()  # Raise an error if the request failed
    
    data = response.json()
    # Assuming the API returns {"output": [[tokens], [tokens], ...]}
    return data.get("output", []), keys

def word_embeddings(tokens, lang="fr") -> list[str]:

    payload = {"input": []}

    for token in tokens:
        payload['input'].append({
            "lang": lang,
            "token": token
        })

    response = requests.post(WORD_EMBEDIDNGS_API_URL, json=payload)
    response.raise_for_status()  # Raise an error if the request failed
    
    data = response.json()
    # Assuming the API returns {"output": [[tokens], [tokens], ...]}
    return data.get("output", [])

def sentence_embeddings(reviews) -> list[str]:

    payload = {"input": reviews}


    response = requests.post(SENTENCE_EMBEDDINGS_API_URL, json=payload)
    response.raise_for_status()  # Raise an error if the request failed
    
    data = response.json()
    # Assuming the API returns {"output": [[tokens], [tokens], ...]}
    return data.get("output", [])
