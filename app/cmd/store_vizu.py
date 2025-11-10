import logging
from postgres.PostgresSingleton import PostgresSingleton
from utils import api_tokenize, api_word_embeddings, api_sentence_embeddings, normalize_to_range

import streamlit as st
import numpy as np
from collections import Counter, defaultdict
from sklearn.cluster import KMeans
from bertopic import BERTopic
from tqdm import tqdm

# -------------------------
# Logging
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -------------------------
# Config
# -------------------------
LANG = "fr"
MIN_FREQ = 0
N_TOPICS = 30

# -------------------------
# Functions
# -------------------------
def tokenize_reviews(reviews, lang):
    all_tokens = set()
    c_tokens = {"review_title": Counter(), "positive_text": Counter(), "negative_text": Counter()}
    all_reviews = [review for review_list in reviews.values() for review in review_list]
    outputs, keys = api_tokenize(all_reviews, lang)
    for output, key in zip(outputs, keys):
        tokens = output.get("tokens", [])
        all_tokens.update(tokens)
        c_tokens[key].update(tokens)
    return c_tokens, all_tokens


def get_token_embeddings(tokens, lang):
    embeddings = {}
    outputs = api_word_embeddings(tokens, lang)
    for output in outputs:
        token = output.get("token")
        if token:
            embeddings[token] = output['emb']
    return embeddings


def get_sentence_embeddings(reviews):
    all_reviews_dict = [review for review_list in reviews.values() for review in review_list]
    
    seen_sentences = set()
    all_reviews_to_emb = []
    display_texts = []
    c = Counter()

    for r in all_reviews_dict:
        for emoji, text_key in [("😍", "positive_text"), ("😡", "negative_text")]:
            text = r.get(text_key)
            if text and text not in seen_sentences:
                c[text_key] += 1
                seen_sentences.add(text)
                all_reviews_to_emb.append(text)
                display_texts.append(f"{emoji} {text}")

    embeddings = api_sentence_embeddings(all_reviews_to_emb)
    return np.array(embeddings), display_texts, c


def fit_topic_model(filtered_keywords, filtered_embeddings, n_topics):
    n_clusters = min(n_topics, len(filtered_keywords))  # Avoid having more clusters than keywords
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    topic_model = BERTopic(hdbscan_model=kmeans, language='french')
    topics, _ = topic_model.fit_transform(filtered_keywords, filtered_embeddings)
    return topic_model, topics


# -------------------------
# Main
# -------------------------
db = PostgresSingleton()
selected_hotels = db.get_all_kalios()
hotel_ids = selected_hotels.index.tolist()

for hotel_id in tqdm(hotel_ids, desc="Processing hotels"):
    d_fig = dict()
    hotel_reviews = db.get_review_texts_by_ids([hotel_id])
    
    num_reviews = len(hotel_reviews.get(hotel_id, []))
    tqdm.write(f"➡️ Processing hotel id {hotel_id} with {num_reviews} reviews")

    if num_reviews == 0:
        logging.info(f"⚠️ Hotel {hotel_id} has no reviews, skipping.")
        continue

    try:
        token_counts, all_tokens = tokenize_reviews(hotel_reviews, LANG)
        token_embeddings = get_token_embeddings(all_tokens, LANG)
        reviews_embeddings, display_reviews, c_sentiment = get_sentence_embeddings(hotel_reviews)
    except Exception as e:
        logging.error(f"❌ Error processing hotel {hotel_id}: {e}")
        tqdm.write(f"❌ Skipping hotel {hotel_id} due to error")
        continue
    
    try:
        # Process positive/negative tokens separately
        for s in ["positive", "negative"]:
            s_token_counts = token_counts[f"{s}_text"]
            filtered_keywords = [t for t in s_token_counts if t in token_embeddings and s_token_counts[t] > MIN_FREQ]
            filtered_freq = [s_token_counts[t] for t in filtered_keywords]
            filtered_embeddings = np.array([token_embeddings[t] for t in filtered_keywords])

            if not filtered_keywords:
                continue

            topic_model, topics = fit_topic_model(filtered_keywords, filtered_embeddings, N_TOPICS)
            if topic_model is None:
                logging.info(f"⚠️ Not enough {s} keywords to fit topic model for hotel {hotel_id}, skipping {s} visualization.")
                continue

            topic_words = defaultdict(Counter)
            for word, freq, label in zip(filtered_keywords, filtered_freq, topics):
                topic_words[label][word] = freq

            topic_labels = {label: " ".join(w for w, _ in c.most_common(3)) for label, c in topic_words.items()}

            try:
                topic_model.set_topic_labels(topic_labels)
            except Exception:
                pass

            fig_interactive = topic_model.visualize_document_datamap(
                docs=filtered_keywords,
                embeddings=filtered_embeddings,
                interactive=True,
                enable_search=False,
                custom_labels=True,
                int_datamap_kwds={
                    "min_fontsize": 12,
                    "max_fontsize": 18,
                    "marker_size_array": normalize_to_range(filtered_freq, new_max=1000),
                    "point_radius_min_pixels": 4,
                    "point_radius_max_pixels": 25,
                    "initial_zoom_fraction": 0.8,
                    "logo_width": 25,
                    "font_family": "Quattrocento",
                }
            )

            d_fig[s] = str(fig_interactive)

        # Full reviews topic model
        if display_reviews:
            topic_model, topics = fit_topic_model(display_reviews, reviews_embeddings, N_TOPICS)
            if topic_model is not None:
                try:
                    topic_model.set_topic_labels(topic_labels)
                except Exception:
                    pass

                fig_interactive = topic_model.visualize_document_datamap(
                    docs=display_reviews,
                    embeddings=reviews_embeddings,
                    interactive=True,
                    enable_search=False,
                    custom_labels=True,
                    int_datamap_kwds={
                        "min_fontsize": 12,
                        "max_fontsize": 18,
                        "marker_size_array": normalize_to_range([len(r.split()) for r in display_reviews], new_max=50),
                        "point_radius_min_pixels": 4,
                        "point_radius_max_pixels": 25,
                        "initial_zoom_fraction": 0.8,
                        "logo_width": 25,
                        "font_family": "Quattrocento",
                    }
                )
                d_fig['review'] = str(fig_interactive)

        # -------------------------
        # Insert visualizations into DB
        # -------------------------
        try:
            db.insert_review_visualization(
                id_kalio=hotel_id,
                positive_html=d_fig.get("positive").strip(),
                negative_html=d_fig.get("negative").strip(),
                reviews_html=d_fig.get("review").strip()
            )
            logging.info(f"✅ Inserted visualization for hotel {hotel_id}")
            tqdm.write(f"✅ Completed hotel {hotel_id}")
        except Exception as e:
            logging.error(f"❌ Failed to insert visualization for hotel {hotel_id}: {e}")

    except Exception as e:
        logging.error(f"❌ Failed to generate visualizations for hotel {hotel_id}: {e}")
        tqdm.write(f"❌ Skipping hotel {hotel_id} due to visualization error")