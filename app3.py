import streamlit as st
import pandas as pd
from supabase import create_client

# 1. Page Config
st.set_page_config(page_title="World Cup 2026", initial_sidebar_state="expanded")

# 2. Styling (CSS)
st.markdown("""
    <style>
    /* Force the header container to have a visible background */
    [data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.5) !important; /* Semi-transparent grey/white */
        border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
    }

    /* Force the sidebar toggle button icon to be black for better visibility */
    button[kind="header"] {
        color: #000000 !important;
    }
    
    /* Ensure the mobile menu/sidebar toggle is always visible */
    [data-testid="stSidebarCollapseButton"] {
        color: #000000 !important;
    }
    
    /* Reduce gap between elements inside containers on mobile */
    [data-testid="stVerticalBlock"] {
        gap: 0.8rem !important;
    }
    
    /* Force Hide the 'Made with Streamlit' footer */
    footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"], .viewerBadge_container__1QSob, .styles_viewerBadge__1yB5_ {
        visibility: hidden !important;
        display: none !important;
    }

    /* Keep hiding the Hamburger Menu */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden;}
        
    /* This targets the metric value text specifically to stop it from being huge */
    [data-testid="stMetricValue"] {
        font-size: 18px !important;
        background-color: #ffffff !important;
        padding: 5px !important;
        border-radius: 10px !important;
        border: 1px solid #e0e0e0 !important;
        margin-bottom: 8px;
    }
    
    /* This targets the metric label */
    [data-testid="stMetricLabel"] {
        font-size: 16px !important;
    }
    
    [data-testid="stAppViewContainer"] { color: #000000 !important; background: linear-gradient(135deg, #66ccff, #ccffff) !important; background-attachment: fixed !important; }
    
    h1, h2, h3, h4, p, span, label { color: #000000 !important; }
    
    .country-box { display: inline-block; min-width: 85px; width: auto; padding: 2px 4px; margin: 2px; border: 1px solid #ddd; border-radius: 5px; text-align: center; background-color: #f9f9f9; font-size: 0.9em; color: black; white-space: nowrap; }
    
    .correct { background-color: #90EE90 !important; border-color: #228B22 !important; }
    
    /* RED COLOR CLASSES FOR ELIMINATED/FAILED COUNTRIES */
    .failed { background-color: #d9534f !important; border-color: #d91111 !important; color: #ffccff !important; }
    
    .stMarkdown p { margin: 2px 0 !important; }
    
    h3 { margin-bottom: 2px !important; padding-bottom: 0px !important; color: black !important; }
    
    /* Styling for the tables to make them stand out from the gradient background */
    [data-testid="stTable"] {
        background-color: #faffb3 !important;
        border-radius: 10px !important;
        padding: 5px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Target the table header for better readability */
    thead tr th {
        background-color: #f0f2f6 !important;
        color: #333 !important;
        font-weight: bold !important;
        text-align: center !important;
    }

    /* Ensure table rows have a clean, non-transparent look */
    tbody tr td {
        background-color: #ffffff !important;
        border-bottom: 1px solid #eee !important;
        padding-left: 20px !important;
        padding-right: 30px !important;
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
    preds = supabase.table("predictions") \
        .select("round, country, participants(user_name)") \
        .order("id") \
        .limit(2000) \
        .execute()
    
    results = supabase.table("test_results") \
        .select("round, country") \
        .order("id") \
        .limit(2000) \
        .execute()
        
    # --- FETCH ELIMINATION STAGE DATA ---
    elim_data = supabase.table("eliminated_teams") \
        .select("country, eliminated_at_stage") \
        .execute()
    
    return preds.data, results.data, elim_data.data

# 5. App Execution
st.title("⚽ World Cup 2026 Predictions")
raw_data, raw_results, raw_eliminated = get_all_data()

# Check if data exists
if not raw_data:
    st.warning("No prediction data found! It looks like the tournament has not started. Check back once predictions are in.")
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

if raw_data is None or len(raw_data) == 0:
    st.info("Loading data from database...")
    st.stop()

# Process Data safely
try:
    flat_data = [{"Player": e.get("participants", {}).get("user_name", "Unknown"), 
                  "Round": e.get("round"), 
                  "Country": e.get("country")} for e in raw_data]
    df = pd.DataFrame(flat_data)
    
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

# --- PROCESS GLOBAL ELIMINATIONS DICTIONARY ---
elim_map = {str(e['country']).lower().strip(): str(e['eliminated_at_stage']).upper().strip() for e in raw_eliminated} if raw_eliminated else {}

# 6. Sidebar
st.sidebar.markdown("### 👤 Player Details")
player_list = sorted(df["Player"].unique())
selected_player = st.sidebar.selectbox("Select Player", player_list)

st.sidebar.markdown(f"**Total Players:** {len(player_list)}")


# 7. Player Detail View
if selected_player:
    st.subheader(f"Predictions by {selected_player}")
    player_preds = df[df["Player"] == selected_player]
    total_score = 0
    score_summary = []
    
    all_stages = ['R32', 'R16', 'QF', 'SF', 'FOURTH', 'THIRD', 'RUNNERUP', 'CHAMPION']
    
    for stage in all_stages:
        stage_upper = stage.upper().strip()
        preds_in_stage = player_preds[player_preds['Round'].str.upper() == stage_upper]
        countries = preds_in_stage['Country'].tolist()
        
        lookup_round = stage_upper
        actuals = [c.lower() for c in results_map.get(lookup_round, [])]        
        
        stage_key = stage.upper()
        
        # Calculate points safely (solely uses actuals results data)
        stage_points = sum(POINTS_MAP.get(stage_key, 0) for c in countries if c.lower() in actuals)
        total_score += stage_points
        
        st.markdown(f"### {stage} ({stage_points} pts)")
        
        if countries:
            has_actuals = len(actuals) > 0
            stage_order = ['R32', 'R16', 'QF', 'SF', 'FOURTH', 'THIRD', 'RUNNERUP', 'CHAMPION']
            
            box_html = ""
            for c in countries:
                c_lower = c.lower().strip()
                status_class = ""
                
                # 1. Check if the team successfully advanced in this round (Green)
                if has_actuals and c_lower in actuals:
                    status_class = "correct"
                
                # 2. Check if the team was eliminated chronologically before or during this round (Red)
                elif c_lower in elim_map:
                    stage_failed = elim_map[c_lower]
                    
                    try:
                        current_stage_idx = stage_order.index(stage_upper)
                        failed_stage_idx = stage_order.index(stage_failed)
                        
                        # Turn RED if current stage column position is equal to or past failure point
                        if current_stage_idx >= failed_stage_idx:
                            status_class = "failed"
                    except ValueError:
                        # Fallback case protection
                        status_class = "failed"
                
                box_html += f'<div class="country-box {status_class}">{c}</div>'
            
            st.markdown(f'<div style="text-align: center;">{box_html}</div>', unsafe_allow_html=True)
            
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
        
        lookup_round = r
        actuals = [x.lower() for x in results_map.get(lookup_round, [])]
        
        if c in actuals:
            total_points += POINTS_MAP.get(r, 0)
                
    leaderboard.append({"Player": player, "Total Points": total_points})

df_leaderboard = pd.DataFrame(leaderboard).sort_values(by="Total Points", ascending=False).reset_index(drop=True)

df_leaderboard_top5 = df_leaderboard.head(5)
st.table(df_leaderboard_top5)

# --- Additional Insights ---
def get_most_guessed(round_name):
    round_data = df[df["Round"].str.upper() == round_name.upper()]
    if not round_data.empty:
        counts = round_data["Country"].value_counts()
        top_2 = counts.head(3)
        results = [f"{country} ({count})" for country, count in top_2.items()]
        return "<br>".join(results)
    return "No data"
    
st.header("📊 Popular Picks")

with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"**Champion**<br>{get_most_guessed('CHAMPION')}", unsafe_allow_html=True)
    with col2:
        st.markdown(f"**RunnerUp**<br>{get_most_guessed('RUNNERUP')}", unsafe_allow_html=True)
    with col3:
        st.markdown(f"**Semi-Finalist**<br>{get_most_guessed('SF')}", unsafe_allow_html=True)
    with col4:
        st.markdown(f"**Quarter-Finalist**<br>{get_most_guessed('QF')}", unsafe_allow_html=True)
        
st.markdown('</div>', unsafe_allow_html=True)

if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()