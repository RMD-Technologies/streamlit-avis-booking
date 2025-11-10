from utils import filter_hotel_to_select, api_tokenize, api_word_embeddings, api_sentence_embeddings, normalize_to_range
from postgres.PostgresSingleton import PostgresSingleton
import streamlit as st
import streamlit.components.v1 as components
from collections import Counter, defaultdict
from sklearn.cluster import KMeans
from bertopic import BERTopic
import numpy as np

db = PostgresSingleton()
selected_hotels = filter_hotel_to_select(is_id_booking=True, is_selected_by_default=False)
hotel_ids = selected_hotels.index.tolist()
hotel_reviews = db.get_review_texts_by_ids(hotel_ids)

if not hotel_reviews or all(len(revs) == 0 for revs in hotel_reviews.values()):
    st.info("ℹ️ Aucun avis disponible pour les hôtels sélectionnés.")
else:
    # -------------------------
    # Config
    # -------------------------
    st.sidebar.header("⚙️ Configuration")

    # Dynamic sidebar inputs
    LANG = st.sidebar.selectbox(
        "Langue de traitement",
        ["fr", "en"],
        index=0,
        help="Choisissez la langue utilisée pour la tokenisation et les embeddings."
    )

    N_TOPICS_TOKENS = st.sidebar.slider(
        "Nombre de topics à extraire (mots)",
        min_value=5,
        max_value=100,
        value=30,
        step=5,
    )

    N_TOPICS_REVIEW = st.sidebar.slider(
        "Nombre de topics à extraire (avis)",
        min_value=5,
        max_value=100,
        value=30,
        step=5,
    )

    MIN_FREQ = st.sidebar.number_input(
        "Fréquence minimale des tokens",
        min_value=0,
        value=0,
        step=1,
        help="Ne considérer que les tokens apparaissant au moins ce nombre de fois."
    )

 
    # Using the dynamic configuration
    st.write(f"Langue sélectionnée : {LANG}")
    st.write(f"Nombre de topics (mots): {N_TOPICS_TOKENS}")
    st.write(f"Nombre de topics (avis): {N_TOPICS_REVIEW}")
    st.write(f"Fréquence minimale : {MIN_FREQ}")


    # -------------------------
    # Caching functions
    # -------------------------
    @st.cache_data(show_spinner="Tokenisation des avis en cours… ⏳")
    def tokenize_reviews(reviews, lang):
        """
        Tokenize all reviews and count frequency of tokens.
        """
        all_tokens = set()
        c_tokens = {"review_title": Counter(), "positive_text": Counter(), "negative_text": Counter()}
        all_reviews = [review for review_list in reviews.values() for review in review_list]
        outputs, keys = api_tokenize(all_reviews, lang)
        for output, key in zip(outputs, keys):
            tokens = output.get("tokens", [])
            all_tokens.update(tokens)
            c_tokens[key].update(tokens)
        return c_tokens, all_tokens


    @st.cache_data(show_spinner="Récupération des word embeddings... 🔄")
    def get_token_embeddings(tokens, lang):
        """
        Fetch embeddings for tokens.
        """
        embeddings = {}
        outputs = api_word_embeddings(tokens, lang)
        for output in outputs:
            token = output.get("token")
            if token:
                embeddings[token] = output['emb']
        return embeddings


    @st.cache_data(show_spinner="Récupération des sentences embeddings... 🔄")
    def get_sentence_embeddings(reviews):
        """
        Fetch embeddings for reviews, avoiding duplicated sentences.
        
        Returns:
            embeddings: np.array of sentence embeddings
            display_texts: list of strings with emoji prefix for visualization
        """
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


    @st.cache_resource
    def fit_topic_model(filtered_keywords, filtered_embeddings, n_topics):
        """
        Fit BERTopic with KMeans as HDBSCAN replacement.
        """
        kmeans = KMeans(n_clusters=n_topics, random_state=42)
        topic_model = BERTopic(hdbscan_model=kmeans, language='french')
        topics, _ = topic_model.fit_transform(filtered_keywords, filtered_embeddings)
        return topic_model, topics


    # -------------------------
    # Tokenization & embeddings
    # -------------------------
    try:
        token_counts, all_tokens = tokenize_reviews(hotel_reviews, LANG)
        token_embeddings = get_token_embeddings(all_tokens, LANG)
        reviews_embeddings, display_reviews, c_sentiment = get_sentence_embeddings(hotel_reviews)
    except Exception as e:
        st.error(f"Erreur lors du chargement des fichiers : {e}")
        st.stop()

    # Example: positive and negative visualizations side by side
    cols = st.columns(2)  # Create two columns

    with st.spinner("🧠 Ajustement des visualisation (cela peut prendre un moment)..."):
        for i, s in enumerate(["positive", "negative"]):
            # Select column
            with cols[i]:
                st.subheader(f"{s.capitalize()}")


                # Filter tokens with embeddings
                s_token_counts = token_counts[f"{s}_text"]
                
                # Number of tokens before filtering
                nb_tokens_before = len(s_token_counts)

                filtered_keywords = [
                    t for t in s_token_counts if t in token_embeddings and s_token_counts[t] > MIN_FREQ
                ]
                filtered_freq = [s_token_counts[t] for t in filtered_keywords]
                filtered_embeddings = np.array([token_embeddings[t] for t in filtered_keywords])
                
                # Number of tokens after filtering
                nb_tokens_after = len(filtered_keywords)

                # -------------------------
                # Fit BERTopic
                # -------------------------
            
                topic_model, topics = fit_topic_model(filtered_keywords, filtered_embeddings, N_TOPICS_TOKENS)

                # -------------------------
                # Build topic labels
                # -------------------------
                topic_words = defaultdict(Counter)
                for word, freq, label in zip(filtered_keywords, filtered_freq, topics):
                    topic_words[label][word] = freq

                topic_labels = {
                    label: " ".join(w for w, _ in c.most_common(3))
                    for label, c in topic_words.items()
                }

                # Update BERTopic labels
                try:
                    topic_model.set_topic_labels(topic_labels)
                except Exception:
                    pass
                
               
                # -------------------------
                # Visualization
                # -------------------------
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

                components.html(str(fig_interactive), height=350)

                st.write(f"Nombre de tokens avant filtrage : {nb_tokens_before}")
                st.write(f"Nombre de tokens après filtrage : {nb_tokens_after}")


                # -------------------------
                # Download button
                # -------------------------
                html_bytes = str(fig_interactive).encode("utf-8")
                st.download_button(
                    label=f"Download {s} HTML",
                    data=html_bytes,
                    file_name=f"{s}_document_datamap.html",
                    mime="text/html"
                )

        st.subheader("Avis Positif / Negatif")

        # -------------------------
        # Fit BERTopic
        # -------------------------
    
        topic_model, topics = fit_topic_model(display_reviews, reviews_embeddings, N_TOPICS_REVIEW)

        # Update BERTopic labels
        try:
            topic_model.set_topic_labels(topic_labels)
        except Exception:
            pass
        
        
        # -------------------------
        # Visualization
        # -------------------------
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


        components.html(str(fig_interactive), height=350)
        st.write(f"Nombre d'avis positifs : {c_sentiment.get('positive_text', 0)}")
        st.write(f"Nombre d'avis negatifs : {c_sentiment.get('negative_text', 0)}")

        # -------------------------
        # Download button
        # -------------------------
        html_bytes = str(fig_interactive).encode("utf-8")
        st.download_button(
            label=f"Download review HTML",
            data=html_bytes,
            file_name=f"review_document_datamap.html",
            mime="text/html"
        )