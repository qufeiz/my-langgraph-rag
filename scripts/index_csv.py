import csv
import uuid
import os
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---- Setup ----
# Init Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME", "rag-demo-index")

# Connect embeddings (using ada-002 to match your existing 1536 dimensions)
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

# Text splitter (500 tokens ~ safe for search)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " "]
)

# ---- Index function ----
def index_csv_data(csv_path: str, user_id: str = "demo-user"):
    docs = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Create a comprehensive text description for each series
            content = f"Series ID: {row['series_id']}\n"
            content += f"Title: {row['title']}\n"
            content += f"Frequency: {row['frequency']} ({row.get('frequency_short', '')})\n"
            content += f"Units: {row['units']} ({row.get('units_short', '')})\n"
            content += f"Seasonality: {row['season']} ({row.get('season_short', '')})\n"

            if row.get('notes'):
                content += f"Notes: {row['notes']}\n"

            if row.get('period_description'):
                content += f"Period Description: {row['period_description']}\n"

            # Chunk the content if it's long
            chunks = splitter.split_text(content)
            for i, chunk in enumerate(chunks):
                docs.append({
                    "id": str(uuid.uuid4()),
                    "text": chunk,
                    "metadata": {
                        "series_id": row['series_id'],
                        "title": row['title'],
                        "frequency": row['frequency'],
                        "units": row['units'],
                        "season": row['season'],
                        "user_id": user_id,
                        "chunk": i,
                        "data_type": "economic_series"
                    }
                })

    # Push to Pinecone via LangChain wrapper
    vstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
    vstore.add_texts(
        texts=[d["text"] for d in docs],
        metadatas=[d["metadata"] for d in docs],
        ids=[d["id"] for d in docs]
    )

    print(f"✅ Uploaded {len(docs)} chunks to Pinecone index `{index_name}`")

# ---- Example run ----
if __name__ == "__main__":
    csv_file = "seriesdatasample.csv"
    print(f"Starting to index {csv_file}...")

    try:
        index_csv_data(csv_file, user_id="series-user")
        print("✅ Successfully indexed all economic series data!")
    except Exception as e:
        print(f"❌ Error indexing documents: {e}")