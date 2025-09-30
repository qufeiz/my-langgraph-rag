import os
import json
from typing import List
from fredapi import Fred
from dotenv import load_dotenv
from langchain.schema import Document

load_dotenv()

class FredTool:
    def __init__(self):
        self.fred = Fred(api_key=os.getenv("FRED_API_KEY"))

    def get_series_data(self, series_id: str) -> dict:
        """Fetch FRED series data and return as JSON"""
        data = self.fred.get_series(series_id, limit=10)  # Only last 10 points for MVP
        info = self.fred.get_series_info(series_id)

        observations = [
            {"date": str(date), "value": float(value)}
            for date, value in zip(data.index, data.values)
            if value == value  # filter NaNs
        ]

        return {
            "series_id": series_id,
            "title": info["title"],
            "units": info["units"],
            "frequency": info["frequency"],
            "recent_data": observations[-5:] if observations else []  # Last 5 points
        }

def enrich_with_fred_data(retrieved_docs: List[Document]) -> List[Document]:
    """Check docs for series IDs and enrich with live FRED data"""
    fred_tool = FredTool()
    enriched_docs = []

    for doc in retrieved_docs:
        series_id = doc.metadata.get("series_id")

        if series_id:
            # Fetch live data
            fred_data = fred_tool.get_series_data(series_id)
            # Create enriched document
            enriched_content = f"{doc.page_content}\n\nLive FRED Data:\n{json.dumps(fred_data, indent=2)}"
            enriched_doc = Document(
                page_content=enriched_content,
                metadata={**doc.metadata, "enriched_with_fred": True}
            )
            enriched_docs.append(enriched_doc)
        else:
            # No series ID, keep original
            enriched_docs.append(doc)

    return enriched_docs