fixed_ngrams = {
    '_': [
        "partie commune",
        "isolation phonique",
        "petits soins",
        "vieux port",
        "produits locaux",
        "seul bémol",
        "centre commercial",
        "rien à signaler"
    ],
    '-': [
        "sèche cheveux",
        "centre ville",
        "micro onde"
    ],
    "": [
        "hyper centre",
        "mini bar",
        "king size"
    ]
}

abbrevation = {
    'oklm': 'au calme',
    'sdb': 'salle_de_bain',
    'rdc': 'rez-de-chaussée',
    'ras': 'rien_à_signaler',
    'pdj': 'petit-déjeuner',
    'we': 'week-end',
    'pb': 'problème',
    'pt': 'petit',
    'dej': 'déjeuner',
    'ptdj': 'petit-déjeuner'
} 

pattern_rules = [
    (r"\bmachine à (\w+)", r"machine_à_\1"),
    (r"\bwi[- ]?fi\b", r"wifi"),
    (r"\bà (2|deux) pas", r"à_deux_pas"),
    (r"\bp[ e]?tits?", r"petit"),
    (r"\bpetits?[- ]?d[ée]j(?:eun[ée]r)?s?\b", r"petit-déjeuner"),
    (r"\b(?:rapport[- ]?)?qualit[ée]s?[ /-]?pri(?:x)?", r"rapport_qualité-prix"),
    (r"\b(salle|jus) de? (?:l |le |la |les )?([\w\s-]+)", r"\1_de_\2"),
    (r"\b(?!(?:manque|pas|peu)\b)(\w+) de (bain|douche|toilette|mer)", r"\1_de_\2"),
    (r"\brez[- ]?de[- ]?chaus(s|ç|ss)er?e?\b", r"rez-de-chaussée"),
    (r"\bbooking[ .]?com\b", r"booking.com"),
    (r"\b(week[- ]?end)\b", r"week-end"),
    (r"\bcheck(?:[- ]?(in|out)|(in|out))\b", r"check-\1\2"),
]