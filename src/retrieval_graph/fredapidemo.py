import os
from fredapi import Fred
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load .env where FRED_API_KEY is stored
load_dotenv()
fred = Fred(api_key=os.getenv("FRED_API_KEY"))

# Fetch series
series_id = "ACTLISCOUMM44940"
title = "Housing Inventory: Active Listing Count MoM in Sumter, SC (CBSA)"

data = fred.get_series(series_id)

info = fred.get_series_info("ACTLISCOUMM44940")
print(info)

# Plot it
plt.figure(figsize=(10, 5))
plt.plot(data.index, data.values)
plt.title(info['title'])
plt.xlabel("Date")
plt.ylabel(info['units'])
plt.grid(True)
plt.show()