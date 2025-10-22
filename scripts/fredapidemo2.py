import os
import json
from fredapi import Fred
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load .env where FRED_API_KEY is stored
load_dotenv()
fred = Fred(api_key=os.getenv("FRED_API_KEY"))

# Choose a series
series_id = "ACTLISCOUMM44940"

# ---- Fetch data ----
data = fred.get_series(series_id)  # pandas Series
info = fred.get_series_info(series_id)  # pandas Series (metadata)

# ---- Prepare JSON (for LLM or API return) ----
observations = [
    {"date": str(date), "value": float(value)}
    for date, value in zip(data.index, data.values)
    if value == value  # filter out NaNs
]

series_json = {
    "series_id": series_id,
    "title": info["title"],
    "units": info["units"],
    "frequency": info["frequency"],
    "seasonality": info["seasonal_adjustment"],
    "observations": observations,
}

# Print to confirm JSON
print(json.dumps(series_json, indent=2)[:500], "...")  # print first 500 chars

# ---- Plot (for frontend / UI) ----
plt.figure(figsize=(10, 5))
plt.plot(data.index, data.values, label=info['title'])
plt.title(info["title"])
plt.xlabel("Date")
plt.ylabel(info["units"])
plt.grid(True)
plt.legend()
plt.tight_layout()

# Save instead of show (useful for API/frontend)
plt.savefig("plot.png")
plt.close()
print("✅ JSON prepared & plot.png saved")