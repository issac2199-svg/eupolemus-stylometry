import os
import re
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity, pairwise_distances
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from collections import Counter
import unicodedata

# CLTK imports
from cltk import NLP

def setup_cltk():
    print("Initializing CLTK...")
    # Instantiate NLP for Ancient Greek. It auto-downloads models if needed.
    cltk_nlp = NLP(language="grc", suppress_banner=True)
    return cltk_nlp

def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def chunk_text(text, chunk_size=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        if len(chunk.split()) >= chunk_size // 2: 
            chunks.append(chunk)
    return chunks

def preprocess_and_extract(cltk_nlp, text, chunk_size=50):
    chunks = chunk_text(text, chunk_size)
    processed_chunks = []
    
    for i, chunk in enumerate(chunks):
        doc = cltk_nlp.analyze(text=chunk)
        lemmas_accented = []
        pos_tags = []
        function_lemmas = []
        
        # Function-word POS categories — matched by substring to handle CLTK
        # tag name variants (e.g. CONJUNCTION, CONJ_COORD, ADP, PREP, PART, etc.)
        FUNCTION_WORD_SUBSTRINGS = ('ADP', 'PREP', 'CONJ', 'PART', 'PRON', 'ADV')

        for word in doc.words:
            # Punctuation check
            if word.pos is not None and 'PUNCTUATION' not in word.pos.name:
                lemma = word.lemma.lower() if word.lemma else word.string.lower()
                lemmas_accented.append(lemma)
                pos = word.pos.name
                pos_tags.append(pos)

                # Function words: match any tag containing a function-word substring
                if any(sub in pos for sub in FUNCTION_WORD_SUBSTRINGS):
                    function_lemmas.append(lemma)
                    
        lemmas_deaccented = [remove_accents(w) for w in lemmas_accented]
        function_lemmas_deaccented = [remove_accents(w) for w in function_lemmas]
        
        # also compute 4-grams for the plain text of the chunk
        plain_text = re.sub(r'[^\w\s]', '', chunk.lower())
        char_4grams = [plain_text[j:j+4] for j in range(len(plain_text)-3)]
        
        processed_chunks.append({
            'chunk_text': chunk,
            'lemmas_accented': " ".join(lemmas_accented),
            'lemmas_deaccented': " ".join(lemmas_deaccented),
            'function_accented': " ".join(function_lemmas),
            'function_deaccented': " ".join(function_lemmas_deaccented),
            'pos_tags': " ".join(pos_tags),
            'char_4grams': " ".join(char_4grams),
            # Raw de-accented lemmas string — used for lexicon-based function-word filter
            'all_lemmas_deaccented_list': lemmas_deaccented,
        })
        
    return processed_chunks

def load_texts():
    with open('text_a.txt', 'r', encoding='utf-8') as f:
        text_a = f.read()
    with open('text_b.txt', 'r', encoding='utf-8') as f:
        text_b = f.read()
    return text_a, text_b

def compute_delta(dtm):
    # Z-score standardization feature-wise
    scaler = StandardScaler(with_mean=True, with_std=True)
    dtm_z = scaler.fit_transform(dtm)
    # Burrows' Delta is equivalent to manhattan distance of z-scores.
    delta_matrix = pairwise_distances(dtm_z, metric='manhattan') / dtm.shape[1]
    return delta_matrix, dtm_z

def analyze_feature(corpus, labels, feature_name, max_features=100):
    vectorizer = CountVectorizer(max_features=max_features, token_pattern=r"(?u)\b\S+\b")
    try:
        dtm = vectorizer.fit_transform(corpus).toarray()
    except ValueError:
        print(f"Skipping {feature_name}: empty vocabulary.")
        return None
    feature_names = vectorizer.get_feature_names_out()
    
    if dtm.shape[1] == 0:
        return None
        
    # Delta
    delta_matrix, dtm_z = compute_delta(dtm)
    
    # Cosine
    cosine_matrix = cosine_similarity(dtm)
    
    # PCA
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(dtm_z)
    
    return {
        'dtm': dtm,
        'dtm_z': dtm_z,
        'feature_names': feature_names,
        'delta_matrix': delta_matrix,
        'cosine_matrix': cosine_matrix,
        'pca_result': pca_result
    }

def main():
    cltk_nlp = setup_cltk()
    text_a, text_b = load_texts()
    print("Texts loaded.")
    
    print("Preprocessing texts and generating chunks...")
    chunks_a = preprocess_and_extract(cltk_nlp, text_a)
    chunks_b = preprocess_and_extract(cltk_nlp, text_b)
    
    all_chunks = chunks_a + chunks_b
    labels = ['PE'] * len(chunks_a) + ['E'] * len(chunks_b)
    chunk_labels = [f"PE_{i+1}" for i in range(len(chunks_a))] + [f"E_{i+1}" for i in range(len(chunks_b))]
    
    df = pd.DataFrame(all_chunks)
    
    results = {}
    print("Running feature analysis and calculating distances...")
    
    features_to_analyze = [
        ('lemmas_accented', 50),
        ('lemmas_deaccented', 50),
        ('function_accented', 30),
        ('function_deaccented', 30),
        ('char_4grams', 100),
        ('pos_tags', 20)
    ]
    
    for feature_type, max_feat in features_to_analyze:
        corpus = df[feature_type].tolist()
        res = analyze_feature(corpus, chunk_labels, feature_type, max_features=max_feat)
        if res is None:
            continue
            
        results[feature_type] = res
        
        # Plot PCA
        plt.figure(figsize=(8, 6))
        for i, label in enumerate(labels):
            color = 'red' if label == 'PE' else 'blue'
            # Only add to legend once per label
            legend_label = label if (i == 0 or i == len(chunks_a)) else ""
            plt.scatter(res['pca_result'][i, 0], res['pca_result'][i, 1], color=color, label=legend_label)
            plt.text(res['pca_result'][i, 0], res['pca_result'][i, 1], chunk_labels[i], fontsize=9)
        plt.title(f'PCA - {feature_type}')
        plt.legend()
        plt.savefig(f'pca_{feature_type}.png')
        plt.close()
        
        # Plot Dendrogram (using Delta matrix)
        # Convert square distance matrix to condensed form
        import scipy.spatial.distance as ssd
        condensed_dist = ssd.squareform(res['delta_matrix'])
        linked = linkage(condensed_dist, 'ward')
        
        plt.figure(figsize=(10, 7))
        dendrogram(linked, labels=chunk_labels, orientation='top', distance_sort='descending', show_leaf_counts=True)
        plt.title(f'Dendrogram (Burrows\' Delta) - {feature_type}')
        plt.tight_layout()
        plt.savefig(f'dendrogram_{feature_type}.png')
        plt.close()

    # Leave-one-out cross-validation with silhouette score
    print("Running Leave-one-out cross-validation with silhouette score...")
    base_res = results['lemmas_deaccented']
    if base_res:
        total_tests = len(all_chunks)
        silhouette_scores = []

        for leave_out_idx in range(total_tests):
            loo_corpus = df['lemmas_deaccented'].tolist()
            loo_corpus.pop(leave_out_idx)
            loo_labels_binary = [0 if l == 'PE' else 1 for i, l in enumerate(labels) if i != leave_out_idx]

            vec = CountVectorizer(max_features=50, token_pattern=r"(?u)\b\S+\b")
            dtm = vec.fit_transform(loo_corpus).toarray()

            if dtm.shape[1] > 1 and len(set(loo_labels_binary)) > 1:
                _, dtm_z = compute_delta(dtm)
                # Silhouette score measures how well each chunk fits its own cluster
                # vs the other cluster. Range: -1 (wrong cluster) to +1 (perfectly separated).
                score = silhouette_score(dtm_z, loo_labels_binary, metric='cosine')
                silhouette_scores.append(score)

        mean_s = np.mean(silhouette_scores)
        std_s = np.std(silhouette_scores)
        print(f"Leave-one-out cross-validation over {total_tests} iterations:")
        print(f"  Mean silhouette score: {mean_s:.4f} (std: {std_s:.4f})")
        print(f"  Min: {min(silhouette_scores):.4f}, Max: {max(silhouette_scores):.4f}")
        print(f"  Iterations with score > 0.0 (correct clustering): {sum(s > 0 for s in silhouette_scores)}/{len(silhouette_scores)}")

    # Generate Top 10 Stylistic Markers Table — function words ONLY
    # We use a curated de-accented Ancient Greek function-word lexicon to
    # filter the MFW vector, bypassing CLTK POS tags entirely.
    # Includes: conjunctions, particles, prepositions, pronouns, adverbs, copula.
    GREEK_FUNCTION_WORDS = {
        # Conjunctions & particles
        'και', 'δε', 'τε', 'αλλα', 'ουν', 'μεν', 'γαρ', 'ιτι', 'οτι', 'ωσ',
        'ωστε', 'ινα', 'επει', 'επειδη', 'εαν', 'ει', 'αν', 'ουδε', 'μηδε',
        'μητε', 'ουτε', 'ητοι', 'ηδη', 'μεντοι', 'τοι', 'που', 'που', 'νυν',
        'μαλιστα', 'αρα', 'γε', 'περ', 'δη', 'αυτε', 'αθαρ',
        # Prepositions
        'εν', 'εκ', 'εξ', 'εις', 'προς', 'απο', 'υπο', 'επι', 'περι', 'παρα',
        'μετα', 'κατα', 'δια', 'αντι', 'αμφι', 'συν', 'υπερ', 'προ',
        # Pronouns — EXCLUDE bare articles (ο, η) and interrogatives (τι) which
        # are too frequent and non-specific to be useful stylistic markers
        'αυτος', 'αυτη', 'αυτο', 'συ', 'εγω', 'ημεις', 'υμεις', 'εκεινος',
        'ουτος', 'τουτο', 'οδε', 'ηδε', 'τοδε', 'τις', 'ος',
        'ιδιος', 'αλληλος',

        # Adverbs
        'ου', 'ουκ', 'ουχ', 'μη', 'ουτε', 'ωδε', 'εκει', 'ενθα', 'τοτε',
        'νυν', 'ετι', 'αει', 'τε', 'αρτι', 'ευθυς', 'ουποτε', 'ουπω', 'μαλιστα',
        'μαλλον', 'ολως', 'παντελως', 'πολυ', 'μονον', 'ουδεποτε',
        # Copula / auxiliary
        'ειμι', 'εστι', 'εστιν',
    }

    res_all = results['lemmas_deaccented']
    if res_all:
        dtm_all = res_all['dtm']
        fn_all = res_all['feature_names']
        # Filter to function words present in MFW
        func_indices = [i for i, f in enumerate(fn_all) if f in GREEK_FUNCTION_WORDS]
        if func_indices:
            dtm_f = dtm_all[:, func_indices]
            fn_f = fn_all[func_indices]
            mean_a_f = np.mean(dtm_f[:len(chunks_a)], axis=0)
            mean_b_f = np.mean(dtm_f[len(chunks_a):], axis=0)
            diff_f = mean_a_f - mean_b_f

            top_n = min(10, len(func_indices))
            top_indices = np.argsort(np.abs(diff_f))[::-1][:top_n]

            # Total tokens per corpus (for length normalization)
            # Each chunk has lemmas_deaccented; count total tokens from the DTM sums
            pe_tokens = int(np.sum(dtm_all[:len(chunks_a)]))   # all features, all PE chunks
            e_tokens  = int(np.sum(dtm_all[len(chunks_a):]))   # all features, all E chunks
            print(f"Total tokens — PE: {pe_tokens}, E: {e_tokens}")

            # Total counts = sum of raw occurrences across all chunks (not normalized)
            total_a_f = np.sum(dtm_f[:len(chunks_a)], axis=0)
            total_b_f = np.sum(dtm_f[len(chunks_a):], axis=0)

            # Normalized rate per 1,000 tokens
            rate_a_f = total_a_f / pe_tokens * 1000
            rate_b_f = total_b_f / e_tokens  * 1000

            # Significance filter: keep only markers that appear at least 4 times
            # in BOTH texts. In a corpus this small, comparing a word that appears
            # 0 or 2 times against another text is mostly noise.
            MIN_RAW_COUNT = 4
            significant_mask = (total_a_f >= MIN_RAW_COUNT) & (total_b_f >= MIN_RAW_COUNT)


            # Re-rank by normalised difference (rate_a - rate_b), take top 10 significant
            norm_diff = rate_a_f - rate_b_f
            # Apply mask then sort
            masked_indices = np.where(significant_mask)[0]
            sorted_masked = masked_indices[np.argsort(np.abs(norm_diff[masked_indices]))[::-1]]
            top_indices = sorted_masked[:10]

            markers_data = []
            for idx in top_indices:
                markers_data.append({
                    'Marker': fn_f[idx],
                    'PE_Total': int(total_a_f[idx]),
                    'E_Total':  int(total_b_f[idx]),
                    'PE_per_1k': round(rate_a_f[idx], 2),
                    'E_per_1k':  round(rate_b_f[idx], 2),
                    'Rate_Diff': round(norm_diff[idx], 2),
                    'Favored_By': 'PE' if norm_diff[idx] > 0 else 'E'
                })

            markers_df = pd.DataFrame(markers_data)
            markers_df.to_csv('stylistic_markers.csv', index=False)
            print(f"Stylistic markers (function words, raw count >= {MIN_RAW_COUNT} in both texts) saved to 'stylistic_markers.csv'.")
            print(markers_df.to_string(index=False))

        else:
            print("No function words found in top MFW — widening to all lemmas.")
            # Fallback: use all lemmas but warn
            dtm_all2 = res_all['dtm']
            mean_a = np.mean(dtm_all2[:len(chunks_a)], axis=0)
            mean_b = np.mean(dtm_all2[len(chunks_a):], axis=0)
            diff = mean_a - mean_b
            top_indices = np.argsort(np.abs(diff))[::-1][:10]
            markers_data = [{'Marker': fn_all[i], 'PE_Mean_Freq': round(mean_a[i], 2),
                             'E_Mean_Freq': round(mean_b[i], 2), 'Difference': round(diff[i], 2),
                             'Favored_By': 'PE' if diff[i] > 0 else 'E'} for i in top_indices]
            markers_df = pd.DataFrame(markers_data)
            markers_df.to_csv('stylistic_markers.csv', index=False)
            print(markers_df.to_string(index=False))
    

    # Print average distance
    if 'lemmas_deaccented' in results:
        res = results['lemmas_deaccented']
        cos_mat = res['cosine_matrix']
        sim_a_b = np.mean(cos_mat[:len(chunks_a), len(chunks_a):])
        print(f"Between-author Cosine Similarity (Lemmas Deaccented): {sim_a_b:.4f}")
        
    print("Analysis complete. Check the directory for PCA plots, Dendrograms, and CSV files.")

if __name__ == "__main__":
    main()
