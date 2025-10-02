import base64
import io
import os
import json
from typing import List

from dotenv import load_dotenv
from fredapi import Fred
from langchain.schema import Document
from matplotlib.figure import Figure

load_dotenv()

class FredTool:
    def __init__(self):
        self.fred = Fred(api_key=os.getenv("FRED_API_KEY"))

    def get_series_data(self, series_id: str) -> dict:
        """Fetch FRED series data, including a preview chart."""
        data = self.fred.get_series(series_id, limit=10)  # Only last 10 points for MVP
        info = self.fred.get_series_info(series_id)

        observations = [
            {"date": str(date), "value": float(value)}
            for date, value in zip(data.index, data.values)
            if value == value  # filter NaNs
        ]

        chart_image = self._create_chart_image(observations, info["title"])

        return {
            "series_id": series_id,
            "title": info["title"],
            "units": info["units"],
            "frequency": info["frequency"],
            "recent_data": observations[-5:] if observations else [],  # Last 5 points
            "chart_image": chart_image,
        }

    def _create_chart_image(self, observations: List[dict], title: str | None) -> str | None:
        """Render data points to a base64-encoded PNG for front-end display."""
        if not observations:
            return None

        figure = Figure(figsize=(6, 3))
        axis = figure.subplots()

        dates = [item["date"] for item in observations]
        values = [item["value"] for item in observations]

        axis.plot(dates, values, marker="o", linewidth=2)
        axis.set_title(title or "FRED Series", fontsize=10)
        axis.set_xlabel("Date")
        axis.set_ylabel("Value")
        axis.grid(True, alpha=0.3)
        axis.tick_params(axis="x", rotation=45)

        buffer = io.BytesIO()
        figure.tight_layout()
        figure.savefig(buffer, format="png", dpi=150)
        buffer.seek(0)

        encoded = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

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
            content_payload = {k: v for k, v in fred_data.items() if k != "chart_image"}
            enriched_content = f"{doc.page_content}\n\nLive FRED Data:\n{json.dumps(content_payload, indent=2)}"
            metadata = {**doc.metadata, "enriched_with_fred": True}
            if fred_data.get("chart_image"):
                metadata["fred_chart_image"] = fred_data["chart_image"]

            enriched_doc = Document(
                page_content=enriched_content,
                metadata=metadata,
            )
            enriched_docs.append(enriched_doc)
        else:
            # No series ID, keep original
            enriched_docs.append(doc)

    return enriched_docs
