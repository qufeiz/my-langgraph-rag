from opensearchpy import OpenSearch

host = "search-my-rag-search-series-only-tl6ign67p2d2spailruowvotau.aos.us-east-1.on.aws"

client = OpenSearch(
    hosts=[{"host": host, "port": 443}],
    http_auth=("qufeiz", "Darky5657#"),   # the one you set in AWS
    use_ssl=True,
    verify_certs=True
)

print(client.info())     # quick health check

# 1) create index (if not exists)
client.indices.create(index="docs", ignore=400)

# 2) insert 1 test document
client.index(
    index="docs",
    id="1",
    body={
        "title": "Test document",
        "content": "This is the first OpenSearch document. Nothing fancy yet."
    }
)

client.indices.refresh(index="docs")

# 3) search it back
res = client.search(
    index="docs",
    body={
        "query": {
            "match": { "content": "first" }
        }
    }
)
print(res["hits"]["hits"])