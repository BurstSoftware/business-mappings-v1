import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# Streamlit app title
st.title("Business Locations Map in Alabama")

# GitHub raw CSV URL (replace with your actual URL)
CSV_URL = "https://raw.githubusercontent.com/username/business-data/main/data/businesses.csv"

# Load the CSV data
@st.cache_data
def load_data(csv_url):
    try:
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return pd.DataFrame()

df = load_data(CSV_URL)

# Check if data is loaded
if df.empty:
    st.stop()

# Initialize geocoder
geolocator = Nominatim(user_agent="business_map_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# Function to geocode city and state
@st.cache_data
def geocode_locations(df):
    locations = []
    for city, state in zip(df["City"], df["State"]):
        try:
            location = geocode(f"{city}, {state}, USA")
            if location:
                locations.append((location.latitude, location.longitude))
            else:
                locations.append((None, None))
        except:
            locations.append((None, None))
        time.sleep(1)  # Respect rate limits
    df["Latitude"] = [loc[0] for loc in locations]
    df["Longitude"] = [loc[1] for loc in locations]
    return df

# Geocode the data
with st.spinner("Geocoding business locations..."):
    df = geocode_locations(df)

# Filter out rows with missing coordinates
df_map = df.dropna(subset=["Latitude", "Longitude"])

# Create a Folium map centered on Alabama
m = folium.Map(location=[32.806671, -86.791130], zoom_start=7)

# Add markers for each business
for idx, row in df_map.iterrows():
    popup_text = f"<b>{row['Business Type']}</b><br>{row['Business Category']}<br>{row['City']}, {row['State']}"
    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=popup_text,
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

# Display the map in Streamlit
st_folium(m, width=700, height=500)

# Display the data table
st.subheader("Business Data")
st.dataframe(df[["Business Category", "Business Type", "City", "State"]])

# Note about missing data
if len(df_map) < len(df):
    st.warning(f"Note: {len(df) - len(df_map)} locations could not be geocoded and are not shown on the map.")
