import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

# 1. Load your CSV file
df = pd.read_csv("dataset-tickets-multi-lang-4-20k.csv")  # assume it has a 'text' column
texts = df["body"].astype(str).tolist()

# 2. Convert text to embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(texts, show_progress_bar=True)

# 3. Create FAISS index
dimension = embeddings[0].shape[0]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# 4. Save the index locally
faiss.write_index(index, "my_faiss.index")

# (Optional) Save mapping to texts for retrieval
df.to_csv("my_faiss_metadata.csv", index=False)

print("✅ FAISS index created and saved locally.")
