# 🧠 NLP Preprocessing Engine

A production-ready Natural Language Processing (NLP) preprocessing pipeline designed to clean, normalize, and transform noisy real-world text into structured data suitable for machine learning models.

---

## 📌 Project Overview

In real-world NLP applications, raw text data is often messy and unstructured. This project builds a **robust, modular preprocessing engine** that handles such data effectively using advanced text cleaning techniques.

The pipeline is designed to be reusable, scalable, and easy to integrate into ML workflows.

---

## 🎯 Objectives

- Clean noisy real-world text data
- Normalize and standardize textual inputs
- Generate meaningful tokens
- Perform token-level statistical analysis
- Build a complete NLP preprocessing pipeline

---

## ⚙️ Features

- ✅ Lowercasing text
- ✅ Removal of numbers
- ✅ Removal of URLs and email patterns
- ✅ Handling repeated characters (e.g., *soooo → so*)
- ✅ Removal of special characters and emojis
- ✅ Removal of extra spaces
- ✅ Tokenization
- ✅ Removal of short tokens (≤ 2 characters, except "no", "not")
- ✅ Error handling for edge cases

---

## 🧪 Sample Input

```python
[
    "Get 100% FREE access now!!!",
    "I absolutely looooved this product 😍😍",
    "Visit https://openai.com now!",
    "Nooooo this is baaad!!!"
]