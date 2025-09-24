import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def initialize_pinecone():
    """Initialize Pinecone client with API key from .env file."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("Error: PINECONE_API_KEY not found in .env file")
        return None

    try:
        pc = Pinecone(api_key=api_key)
        return pc
    except Exception as e:
        print(f"Error initializing Pinecone client: {e}")
        return None


def list_all_ids(index, namespace: str = ""):
    """List all vector IDs in the namespace."""
    try:
        all_ids = []
        # Use list_paginated to get all IDs
        for ids_batch in index.list_paginated(namespace=namespace):
            # ids_batch is a ListResponse object, need to get the vectors
            if hasattr(ids_batch, 'vectors'):
                batch_ids = [v.id for v in ids_batch.vectors]
            else:
                # Try accessing as list directly
                batch_ids = list(ids_batch)
            all_ids.extend(batch_ids)
        return all_ids
    except Exception as e:
        print(f"Error with list_paginated: {e}")
        # Fallback to query method to get IDs
        try:
            print("Trying alternative method to get vector IDs...")
            # Query with dummy vector to get actual IDs
            dummy_vector = [0.0] * 1536  # Use the dimension from stats
            results = index.query(vector=dummy_vector, top_k=10000, include_metadata=True, namespace=namespace)
            return [match.id for match in results.matches]
        except Exception as e2:
            print(f"Error with query fallback: {e2}")
            return []


def fetch_all_with_metadata(index, ids, namespace: str = ""):
    """Fetch all vectors + metadata by ID batches."""
    if not ids:
        return {}

    results = {}
    batch_size = 100

    try:
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i+batch_size]
            resp = index.fetch(ids=batch, namespace=namespace)

            # Handle FetchResponse object
            if hasattr(resp, 'vectors'):
                results.update(resp.vectors)
            elif hasattr(resp, 'to_dict'):
                # Convert to dict and extract vectors
                resp_dict = resp.to_dict()
                if "vectors" in resp_dict:
                    results.update(resp_dict["vectors"])
            else:
                print(f"Warning: Unexpected response format for batch {i//batch_size + 1}")

        return results
    except Exception as e:
        print(f"Error fetching vectors: {e}")
        return {}


def display_vector_info(vectors):
    """Display information about the vectors."""
    if not vectors:
        print("No vectors found in the database.")
        return

    print(f"Found {len(vectors)} vectors in the database:\n")

    for vid, data in vectors.items():
        print(f"ID: {vid}")

        # Handle Vector object attributes
        if hasattr(data, 'metadata'):
            metadata = data.metadata or {}
        else:
            metadata = data.get("metadata", {}) if hasattr(data, 'get') else {}

        if metadata:
            print("  Metadata:")
            for key, value in metadata.items():
                print(f"    {key}: {value}")
        else:
            print("  Metadata: None")

        # Handle Vector object values
        if hasattr(data, 'values'):
            values = data.values or []
        else:
            values = data.get("values", []) if hasattr(data, 'get') else []

        print(f"  Vector dimension: {len(values)}")
        print("-" * 50)


def clean_database(index, namespace: str = ""):
    """Delete all vectors from the specified namespace."""
    try:
        print(f"Cleaning namespace: {'(default)' if not namespace else namespace}")

        # Option 1: Delete all vectors in namespace
        result = index.delete(delete_all=True, namespace=namespace)
        print(f"Cleanup result: {result}")

        # Verify cleanup
        stats = index.describe_index_stats()
        remaining_count = stats.get("namespaces", {}).get(namespace, {}).get("vector_count", 0)
        print(f"Remaining vectors: {remaining_count}")

        return True
    except Exception as e:
        print(f"Error cleaning database: {e}")
        return False


def main():
    # Initialize Pinecone
    pc = initialize_pinecone()
    if not pc:
        return

    try:
        # List all indexes
        indexes = pc.list_indexes()
        print("Available indexes:")
        for idx in indexes:
            print(f"  - {idx.name}")
        print()

        # Connect to the index
        index_name = os.getenv("PINECONE_INDEX_NAME", "rag-demo-index")
        print(f"Connecting to index: {index_name}")
        index = pc.Index(index_name)

        # Get index stats
        stats = index.describe_index_stats()
        print(f"Index stats: {stats}")
        print()

        # Check different namespaces
        namespaces = stats.get("namespaces", {""})
        if isinstance(namespaces, dict):
            namespace_list = list(namespaces.keys())
        else:
            namespace_list = [""]  # default namespace

        if not namespace_list or namespace_list == [None]:
            namespace_list = [""]

        print(f"Found namespaces: {namespace_list}")
        print()

        # Ask user what they want to do
        print("\nWhat would you like to do?")
        print("1. List all vectors (default)")
        print("2. Clean database (delete all vectors)")
        choice = input("Enter choice (1 or 2): ").strip() or "1"

        if choice == "2":
            confirm = input("Are you sure you want to delete ALL vectors? (yes/no): ").strip().lower()
            if confirm == "yes":
                for namespace in namespace_list:
                    if clean_database(index, namespace):
                        print(f"Successfully cleaned namespace: {'(default)' if not namespace else namespace}")
                    else:
                        print(f"Failed to clean namespace: {'(default)' if not namespace else namespace}")
            else:
                print("Operation cancelled.")
        else:
            # List vectors in each namespace
            for namespace in namespace_list:
                namespace_display = namespace if namespace else "(default)"
                print(f"=== Namespace: {namespace_display} ===")

                # Get all IDs
                ids = list_all_ids(index, namespace)
                print(f"Found {len(ids)} vector IDs")

                if ids:
                    # Fetch all vectors with metadata
                    vectors = fetch_all_with_metadata(index, ids, namespace)
                    display_vector_info(vectors)
                else:
                    print("No vectors found in this namespace.")
                print()

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your index name 'rag-demo-index' exists and is accessible.")


if __name__ == "__main__":
    main()