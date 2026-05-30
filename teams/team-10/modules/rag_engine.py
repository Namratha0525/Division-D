import os
import re
import numpy as np
import pandas as pd
import faiss
import logging

from modules.data_loader import load_cpcb_data, load_swachh_bharat_data, load_epr_data

logger = logging.getLogger("RAGEngine")

def tokenize(text):
    return re.findall(r'\w+', text.lower())

class SimpleTFIDF:
    def __init__(self):
        self.vocab = {}
        self.idf = {}
        
    def fit(self, docs):
        all_words = set()
        doc_tokens = []
        for doc in docs:
            tokens = tokenize(doc)
            doc_tokens.append(tokens)
            all_words.update(tokens)
            
        self.vocab = {word: i for i, word in enumerate(sorted(all_words))}
        
        num_docs = len(docs)
        word_doc_counts = {word: 0 for word in self.vocab}
        for tokens in doc_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                if token in word_doc_counts:
                    word_doc_counts[token] += 1
                    
        for word, count in word_doc_counts.items():
            self.idf[word] = np.log((1 + num_docs) / (1 + count)) + 1
            
    def transform(self, docs):
        matrix = []
        vocab_len = len(self.vocab)
        for doc in docs:
            vector = np.zeros(vocab_len)
            tokens = tokenize(doc)
            if not tokens:
                matrix.append(vector)
                continue
            tf = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            for token, count in tf.items():
                if token in self.vocab:
                    idx = self.vocab[token]
                    vector[idx] = (count / len(tokens)) * self.idf[token]
            matrix.append(vector)
        return np.array(matrix)

class FAISSStore:
    def __init__(self, chunks):
        self.chunks = chunks
        self.vectorizer = SimpleTFIDF()
        self.vectorizer.fit(chunks)
        
        vectors = self.vectorizer.transform(chunks)
        dim = vectors.shape[1]
        
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(vectors.astype(np.float32))
        
    def search(self, query, k=3):
        query_vector = self.vectorizer.transform([query])
        D, I = self.index.search(query_vector.astype(np.float32), k)
        
        results = []
        for idx in I[0]:
            if 0 <= idx < len(self.chunks):
                results.append(self.chunks[idx])
        return results

class HybridRAGEngine:
    def __init__(self):
        # 1. Load data
        cpcb_df = load_cpcb_data()
        sbm_df = load_swachh_bharat_data()
        epr_df = load_epr_data()
        
        # 2. Convert to chunks
        self.chunks = []
        
        for _, row in cpcb_df.iterrows():
            chunk = (
                f"CPCB Plastic Waste Management Rules context: State of {row['state_name']} generates "
                f"{row['state_annual_plastic_waste_tonnes']} tonnes of plastic waste annually, "
                f"with an average per capita generation of {row['average_per_capita_g_day']} g/day "
                f"and a recycling rate of {row['recycling_rate_pct']}%."
            )
            self.chunks.append(chunk)
            
        for _, row in sbm_df.iterrows():
            chunk = (
                f"Swachh Bharat Mission (SBM) municipal context: {row['district_name']} district in "
                f"{row['state_name']} state has an institutional monthly average plastic waste generation of "
                f"{row['district_monthly_avg_kg_per_institution']} kg and a municipal collection rate of "
                f"{row['municipal_collection_rate_pct']}%."
            )
            self.chunks.append(chunk)
            
        for _, row in epr_df.iterrows():
            chunk = (
                f"Extended Producer Responsibility (EPR) context: CPCB Category {row['epr_category']} "
                f"(average recycling target: {row['average_recycling_target_pct']}%) has "
                f"{row['national_registered_brands_count']} registered brands nationally and a total CPCB industry "
                f"offset of {row['cpcb_industry_offset_tonnes']} tonnes."
            )
            self.chunks.append(chunk)
            
        # 3. Store embeddings using FAISS
        self.store = FAISSStore(self.chunks)
        
    def retrieve_context(self, state: str, district: str, categories: list) -> str:
        # Retrieve context for state, district, and categories
        query_state_district = f"{state} {district}"
        cpcb_sbm_contexts = self.store.search(query_state_district, k=4)
        
        epr_contexts = []
        for cat in categories:
            epr_contexts.extend(self.store.search(cat, k=1))
            
        # Combine unique contexts
        all_contexts = list(dict.fromkeys(cpcb_sbm_contexts + epr_contexts))
        return "\n".join(all_contexts)
