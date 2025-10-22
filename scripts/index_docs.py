import json
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
def index_docs_from_json(json_path: str, user_id: str = "demo-user"):
    # Load JSON
    with open(json_path, "r") as f:
        data = json.load(f)

    docs = []
    for item in data:
        # Chunk the "Content"
        chunks = splitter.split_text(item["Content"])
        for i, chunk in enumerate(chunks):
            docs.append({
                "id": str(uuid.uuid4()),
                "text": chunk,
                "metadata": {
                    "title": item["Title"],
                    "subtitle": item.get("Subtitle", ""),
                    "date": item.get("Date", ""),
                    "url": item.get("URL", ""),
                    "user_id": user_id,
                    "chunk": i
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
    json_file = "news_posts_full.json"
    print(f"Starting to index {json_file}...")

    try:
        index_docs_from_json(json_file, user_id="news-user")
        print("✅ Successfully indexed all news posts!")
    except Exception as e:
        print(f"❌ Error indexing documents: {e}")