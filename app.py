import streamlit as st
import pandas as pd
from supabase import create_client

# 1. Setup Supabase connection using Streamlit secrets
# In Streamlit Cloud, you will add these in the 'Secrets' settings
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("World Cup 2026 Predictions Dashboard")

# 2. Fetch data from Supabase
def get_data():
    response = supabase.table("predictions").select("*").execute()
    return pd.DataFrame(response.data)

df = get_data()

# 3. Simple Display: Leaderboard/Summary
st.subheader("Champion Predictions Summary")
if not df.empty:
    # Filter for Champion round and count predictions
    champions = df[df['round'] == 'Champion']
    counts = champions['country'].value_counts()
    
    st.bar_chart(counts)
else:
    st.write("No predictions found in the database yet.")

# 4. Show raw table for players to search their name
st.subheader("All Predictions")
st.dataframe(df)