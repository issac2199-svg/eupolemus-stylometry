# Eupolemus Stylometric Analysis

A computational stylometry project comparing the authorship of **Pseudo-Eupolemus** (Fragment 1) and **Eupolemus** (Fragments 2–5) using a suite of quantitative linguistic methods suitable for Ancient Greek texts.

## Overview

This project applies state-of-the-art stylometric techniques to assess whether Pseudo-Eupolemus and Eupolemus share the same authorial voice. The analysis draws on multiple complementary feature representations and statistical distance measures, framed for academic publication standards.

## Methods

| Method | Description |
|---|---|
| **Lemmatization** | Full morphological lemmatization via CLTK (Classical Language Toolkit), with both accented and de-accented variants |
| **Most Frequent Words (MFW)** | Top-N most frequent lemmas used as stylometric fingerprints |
| **Character n-grams** | Character 4-gram frequency profiles for surface-level stylistic capture |
| **POS Tagging** | Part-of-speech tag sequences as syntactic stylistic markers |
| **Burrows' Delta** | Manhattan distance of z-scored feature vectors — the standard authorship attribution measure |
| **Cosine Similarity** | Vector-space similarity between text chunks |
| **PCA** | Principal Component Analysis for 2D visualization of stylistic clustering |
| **Dendrogram** | Hierarchical clustering using Ward linkage on the Burrows' Delta matrix |
| **Leave-one-out Validation** | Cross-validation to assess robustness of cluster stability |
| **Stylistic Markers Table** | Top 10 features most differentiating PE from E, saved to CSV |

## Project Structure

```
eupolemus-stylometry/
├── analysis.py              # Main analysis script
├── text_a.txt               # Pseudo-Eupolemus source text (Fragment 1)
├── text_b.txt               # Eupolemus source text (Fragments 2–5)
├── requirements.txt         # Python dependencies
├── stylistic_markers.csv    # Top 10 differentiating stylistic markers (output)
├── pca_lemmas_accented.png          # PCA plot — accented lemmas
├── pca_lemmas_deaccented.png        # PCA plot — de-accented lemmas
├── pca_char_4grams.png              # PCA plot — character 4-grams
├── pca_pos_tags.png                 # PCA plot — POS tags
├── dendrogram_lemmas_accented.png   # Dendrogram — accented lemmas
├── dendrogram_lemmas_deaccented.png # Dendrogram — de-accented lemmas
├── dendrogram_char_4grams.png       # Dendrogram — character 4-grams
└── dendrogram_pos_tags.png          # Dendrogram — POS tags
```

Labels used in plots:
- **PE** = Pseudo-Eupolemus (Fragment 1)
- **E** = Eupolemus (Fragments 2–5)

## Installation

**Requirements:** Python 3.8+

```bash
git clone https://github.com/issac2199-svg/eupolemus-stylometry.git
cd eupolemus-stylometry
pip install -r requirements.txt
```

CLTK will automatically download the Ancient Greek language models on first run.

## Usage

```bash
python analysis.py
```

The script will:
1. Load and chunk the two source texts into 50-word segments
2. Lemmatize and tag each chunk using CLTK's Ancient Greek pipeline
3. Extract feature vectors (lemmas, character n-grams, POS tags)
4. Compute Burrows' Delta and Cosine Similarity matrices
5. Generate PCA plots and Dendrograms (saved as `.png` files)
6. Run Leave-one-out cross-validation
7. Save the top 10 distinguishing stylistic markers to `stylistic_markers.csv`

## Dependencies

- [CLTK](https://cltk.org/) — Classical Language Toolkit for lemmatization and POS tagging of Ancient Greek
- [scikit-learn](https://scikit-learn.org/) — PCA, vectorization, cosine similarity
- [scipy](https://scipy.org/) — Hierarchical clustering and dendrogram generation
- [matplotlib](https://matplotlib.org/) — Plotting
- [pandas](https://pandas.pydata.org/) — Data handling
- [numpy](https://numpy.org/) — Numerical computation

## Citation

If you use this code or results in academic work, please cite appropriately and credit the use of CLTK:

> Johnson, K. P., et al. (2021). The Classical Language Toolkit: An NLP Framework for Pre-Modern Languages. *ACL Anthology*.
