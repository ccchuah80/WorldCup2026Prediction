import streamlit as st
import pandas as pd
from supabase import create_client

# 1. Page Config
st.set_page_config(page_title="World Cup 2026", initial_sidebar_state="expanded")

# 2. Styling (CSS)
st.markdown("""
    <style>
    /* Force Hide the 'Made with Streamlit' footer */
    footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"], .viewerBadge_container__1QSob, .styles_viewerBadge__1yB5_ {
        visibility: hidden !important;
        display: none !important;
    }

    /* Keep hiding the Hamburger Menu */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden;}
    
    [data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #66ccff, #ccffff) !important; background-attachment: fixed !important; }
    h1, h2, h3, h4, p, div, span, label { color: #000000 !important; }
    .country-box { display: inline-block; min-width: 85px; width: auto; padding: 2px 4px; margin: 2px; border: 1px solid #ddd; border-radius: 5px; text-align: center; background-color: #f9f9f9; font-size: 0.9em; color: black; white-space: nowrap; }
    .correct { background-color: #90EE90 !important; border-color: #228B22 !important; }
    .stMarkdown p { margin: 2px 0 !important; }
    h3 { margin-bottom: 2px !important; padding-bottom: 0px !important; color: black !important; }
    /* Styling for the tables to make them stand out from the gradient background */
    [data-testid="stTable"] {
        background-color: #ffffff !important;
        border-radius: 5px !important;
        padding: 5px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Target the table header for better readability */
    thead tr th {
        background-color: #f0f2f6 !important;
        color: #333 !important;
        font-weight: bold !important;
    }

    /* Ensure table rows have a clean, non-transparent look */
    tbody tr td {
        background-color: #ffffff !important;
        border-bottom: 1px solid #eee !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Constants
POINTS_MAP = {
    'R32': 1, 'R16': 2, 'QF': 4, 'SF': 7, 
    'FOURTH': 0, 'THIRD': 11, 'RUNNERUP': 8, 'CHAMPION': 17
}

# 4. Connection & Data Fetching
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

@st.cache_data(ttl=600)
def get_all_data():
    preds = supabase.table("predictions").select("round, country, participants(user_name)").execute()
    results = supabase.table("test_results").select("round, country").execute()
    return preds.data, results.data

# 5. App Execution
st.title("⚽ World Cup 2026 Predictions")
raw_data, raw_results = get_all_data()

# Robust check to prevent KeyError
if raw_data is None or len(raw_data) == 0:
    st.info("Loading data from database...")
    st.stop() # Wait for data before continuing

# Process Data safely
try:
    flat_data = [{"Player": e.get("participants", {}).get("user_name", "Unknown"), 
                  "Round": e.get("round"), 
                  "Country": e.get("country")} for e in raw_data]
    df = pd.DataFrame(flat_data)
    
    # Double-check that columns exist before proceeding
    if "Player" not in df.columns:
        st.error("Data structure mismatch. Please check your Supabase table schema.")
        st.stop()
        
except Exception as e:
    st.error(f"Error processing data: {e}")
    st.stop()

results_map = {}
for entry in raw_results:
    r = str(entry['round']).upper()
    results_map.setdefault(r, []).append(entry['country'])

# 6. Sidebar
st.sidebar.markdown("### 👤 Player Details")
player_list = sorted(df["Player"].unique())
selected_player = st.sidebar.selectbox("Select Player", player_list)

# Add Total Player count
st.sidebar.markdown(f"**Total Players:** {len(player_list)}")


# 7. Player Detail View
if selected_player:
    st.subheader(f"Predictions by {selected_player}")
    player_preds = df[df["Player"] == selected_player]
    total_score = 0
    score_summary = []
    
    all_stages = ['R32', 'R16', 'QF', 'SF', 'FOURTH', 'THIRD', 'RUNNERUP', 'CHAMPION']
    
    for stage in all_stages:
        stage_upper = stage.upper()
        preds_in_stage = player_preds[player_preds['Round'].str.upper() == stage_upper]
        countries = preds_in_stage['Country'].tolist()
        
# Use this for both Section 7 and Section 8
# Because you now have real SF data, we stop looking at QF for SF points
        lookup_round = stage_upper
        actuals = [c.lower() for c in results_map.get(lookup_round, [])]        
        
        # Ensure we are using the exact same uppercase key for lookup
        stage_key = stage.upper()
        
        # Calculate points
        # We look up the country in 'actuals' and add the points defined in POINTS_MAP
        stage_points = sum(POINTS_MAP.get(stage_key, 0) for c in countries if c.lower() in actuals)
        total_score += stage_points
        
        st.markdown(f"### {stage} ({stage_points} pts)")
        
        if countries:
            has_actuals = len(actuals) > 0
            
            # Display boxes (always show them, highlight if correct)
            box_html = "".join([
                f'<div class="country-box {"correct" if (has_actuals and c.lower() in actuals) else ""}">{c}</div>' 
                for c in countries
            ])
            st.markdown(f'<div style="text-align: center;">{box_html}</div>', unsafe_allow_html=True)
            
            # UPDATED: Added podium stages to the balance logic
            if has_actuals:
                picked_lower = [c.lower() for c in countries]
                balance = [c for c in actuals if c not in picked_lower]
                if balance:
                    st.markdown(f"**(Missed {len(balance)} teams):**")
                    balance_html = "".join([f'<div class="country-box" style="border-color: #d9534f; background-color: #ffe6e6;">{c.title()}</div>' for c in balance])
                    st.markdown(f'<div style="text-align: center;">{balance_html}</div>', unsafe_allow_html=True)
        else:
            st.write("No prediction made.")
        
        st.divider()
        score_summary.append(f"**{stage}**: {stage_points} pts")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Score Summary")
    for line in score_summary:
        st.sidebar.markdown(line)
    st.sidebar.metric("Total Points", total_score)
    
# 8. Leaderboard
st.header("🏆 Score Standing")
leaderboard = []

for player in player_list:
    p_df = df[df["Player"] == player]
    total_points = 0
    
    for _, row in p_df.iterrows():
        r = str(row['Round']).upper()
        c = str(row['Country']).lower()
        
        # Determine the round to look up (if you have SF data, just look up 'SF')
        lookup_round = r
        
        # Get the actual results for this specific round
        actuals = [x.lower() for x in results_map.get(lookup_round, [])]
        
        # If the predicted country is in the actual results for that round, add points
        if c in actuals:
            total_points += POINTS_MAP.get(r, 0)
                
    leaderboard.append({"Player": player, "Total Points": total_points})

# Create and display the table
df_leaderboard = pd.DataFrame(leaderboard).sort_values(by="Total Points", ascending=False).reset_index(drop=True)

# Limit to top 8 players
df_leaderboard_top8 = df_leaderboard.head(8)
st.table(df_leaderboard_top8)
# st.table(df_leaderboard)

if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
