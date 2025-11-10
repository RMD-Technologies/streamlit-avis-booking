import requests

SENTENCES = [
    "L'hôtel est bien placé, super sympa !",
    "Le personnel était très accueillant et serviable.",
    "La chambre était propre mais un peu petite.",
    "Le petit-déjeuner était varié et délicieux.",
    "L'emplacement est parfait pour visiter la ville.",
    "La piscine et le spa étaient vraiment agréables.",
    "Le wifi ne fonctionnait pas très bien dans la chambre.",
    "Le rapport qualité-prix est correct pour cette région.",
    "Le bruit de la rue était un peu dérangeant la nuit.",
    "J'ai beaucoup apprécié la décoration et l'ambiance de l'hôtel."
]

# response = requests.post(
#     "http://127.0.0.1:8000/predict",
#     json={"input": [{"lang": "en", "text": s} for s in SENTENCES]}
# )

response = requests.post(
    "http://127.0.0.1:8000/predict",
    json={    "input": [{"lang": "fr", "token": token} for s in SENTENCES for token in s.split()]
}
)

# response = requests.post(
#     "http://127.0.0.1:8000/predict",
#     json={"input": SENTENCES}
# )

print(response.json())
