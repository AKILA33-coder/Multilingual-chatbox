import streamlit as st
import sqlite3
from textblob import TextBlob
import plotly.graph_objects as go
from datetime import datetime
import random
import html

# ================== DATABASE SETUP ==================
conn = sqlite3.connect("project_db.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_name TEXT,
    user_message TEXT,
    ai_reply TEXT,
    mood TEXT,
    polarity REAL,
    tags TEXT,
    reflection TEXT,
    timestamp TEXT
)
""")
conn.commit()

# ================== HELPERS ==================
def analyze_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        mood = "Happy"
    elif polarity < -0.1:
        mood = "Sad"
    else:
        mood = "Neutral"
    return mood, polarity

def get_suggestion(mood):
    suggestions = {
        "Happy": [
            "🎵 Song: 'Vaathi Coming' – Thalapathy Vibe Song!",
            "🎬 Movie: 'Good Night' – feel-good Tamil movie.",
            "📚 Book: 'Ikigai' – Japanese secret to happiness.",
            "🎨 Try painting or doodling your mood!",
            "🍦 Treat yourself with ice cream!"
        ],
        "Sad": [
            "🎵 Song: 'Nee Partha Vizhigal' – soulful melody.",
            "🎬 Movie: 'Oh My Kadavule' – heartwarming story.",
            "📚 Book: 'The Power of Now' – emotional healing.",
            "🧘 Try short meditation or deep breathing.",
            "💬 Message a friend or write your feelings."
        ],
        "Neutral": [
            "🎵 Song: 'Aarambam Theme' – motivating!",
            "🎬 Movie: 'Mahanati' – inspiring biopic.",
            "📚 Book: 'Atomic Habits' – small changes, big results.",
            "🎮 Play a quick puzzle or chill game.",
            "☕ Brew your favorite drink and relax."
        ]
    }
    return random.choice(suggestions[mood])

def save_chat(chat_name, user_msg, ai_msg, mood, polarity, tags, reflection):
    cursor.execute("""
        INSERT INTO chat_history (chat_name, user_message, ai_reply, mood, polarity, tags, reflection, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (chat_name, user_msg, ai_msg, mood, polarity, tags, reflection, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def fetch_chats(chat_name):
    cursor.execute("SELECT user_message, ai_reply, timestamp FROM chat_history WHERE chat_name = ? ORDER BY id ASC", (chat_name,))
    return cursor.fetchall()

def fetch_chat_names():
    cursor.execute("SELECT DISTINCT chat_name FROM chat_history ORDER BY id DESC")
    return [row[0] for row in cursor.fetchall()]

def fetch_all():
    cursor.execute("SELECT mood, polarity, timestamp FROM chat_history ORDER BY timestamp ASC")
    return cursor.fetchall()

def delete_chat(chat_name):
    cursor.execute("DELETE FROM chat_history WHERE chat_name = ?", (chat_name,))
    conn.commit()

# ================== STREAMLIT UI ==================
st.set_page_config(page_title="MULTILINGUAL CHATBOX", layout="wide")

# --- CSS ---
st.markdown("""
<style>
main {padding-bottom: 120px !important;}
.chat-container {
    max-height: 70vh; overflow-y: auto; padding: 12px 20px;
    border-radius: 15px; background: linear-gradient(180deg, #fff, #f5f5ff);
    box-shadow: inset 0 0 10px rgba(0,0,0,0.05);
}
.chat-bubble-user {background-color: #dcf8c6; padding: 12px; border-radius: 12px; margin: 8px 0; text-align: right; max-width: 80%; margin-left: 20%; box-shadow: 0 2px 6px rgba(0,0,0,0.1);}
.chat-bubble-ai {background-color: #e6e6fa; padding: 12px; border-radius: 12px; margin: 8px 0; text-align: left; max-width: 80%; margin-right: 20%; box-shadow: 0 2px 6px rgba(0,0,0,0.1);}
.input-container {position: fixed; bottom: 0; left: 0; right: 0; background-color: white; padding: 10px 18px; border-top: 1px solid #ddd; box-shadow: 0 -2px 8px rgba(0,0,0,0.06); z-index: 999;}
.stTextInput>div>div>input {border-radius: 10px; padding: 10px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#6C63FF;'>💫 MULTILINGUAL CHATBOX💫</h1>", unsafe_allow_html=True)

# ================== SIDEBAR ==================
st.sidebar.header("💬 Chat Sessions")
chat_names = fetch_chat_names()
selected_chat = st.sidebar.selectbox("Choose Chat:", chat_names) if chat_names else None

new_chat_name = st.sidebar.text_input("🆕 Start New Chat", placeholder="Enter chat name...")
if st.sidebar.button("Create Chat") and new_chat_name.strip():
    st.session_state.active_chat = new_chat_name.strip()
    st.rerun()

if selected_chat:
    if "confirm_clear" not in st.session_state:
        st.session_state.confirm_clear = False
    if st.sidebar.button("🗑️ Clear This Chat"):
        st.session_state.confirm_clear = True
    if st.session_state.confirm_clear:
        st.sidebar.warning(f"⚠️ Confirm delete chat '{selected_chat}'?")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("✅ Yes"):
                delete_chat(selected_chat)
                st.sidebar.success("Chat cleared!")
                st.session_state.confirm_clear = False
                st.rerun()
        with col2:
            if st.button("❌ No"):
                st.session_state.confirm_clear = False
                st.rerun()

# ================== BEAUTIFUL 3D MOOD GRAPH ==================
with st.sidebar.expander("📊 Mood Analyzer"):

    data = fetch_all()
    if data:
        moods = [row[0] for row in data]
        counts = {
            "Happy": sum(1 for m in moods if m == "Happy"),
            "Sad": sum(1 for m in moods if m == "Sad"),
            "Neutral": sum(1 for m in moods if m == "Neutral")
        }

        x = ["Happy", "Sad", "Neutral"]
        y = [0, 0, 0]  # Y-axis just placeholder
        dz = [counts[m] for m in x]  # Z = height of bars
        colors = ['#4CAF50','#E91E63','#FFC107']

        fig = go.Figure()
        for i in range(len(x)):
            fig.add_trace(go.Scatter3d(
                x=[x[i], x[i]],
                y=[y[i], y[i]],
                z=[0, dz[i]],
                mode='lines+markers',
                line=dict(color=colors[i], width=20),
                marker=dict(size=5, color=colors[i]),
                name=f"{x[i]}: {dz[i]}",
                hovertemplate=f"{x[i]}: {dz[i]}"
            ))

        fig.update_layout(
            title="🌈 Mood Summary",
            scene=dict(
                xaxis_title="Mood",
                yaxis_title="",
                zaxis_title="Count",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                zaxis=dict(showgrid=True)
            ),
            margin=dict(l=0, r=0, b=0, t=50),
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No mood data yet. Start chatting!")

# ================== MAIN CHAT ==================
if "active_chat" not in st.session_state:
    st.session_state.active_chat = selected_chat or "Chat 1"

st.subheader(f"🗨️ Chat: {st.session_state.active_chat}")
chat_history = fetch_chats(st.session_state.active_chat)
st.markdown("<div id='chat-box' class='chat-container'>", unsafe_allow_html=True)
for user_msg, ai_reply, time_ in chat_history:
    st.markdown(f"<div class='chat-bubble-user'><b>You:</b> {html.escape(user_msg)}<br><small>{time_}</small></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chat-bubble-ai'><b>AI:</b> {html.escape(ai_reply)}<br><small>{time_}</small></div>", unsafe_allow_html=True)
st.markdown("<div id='end-of-chat'></div></div>", unsafe_allow_html=True)

# ================== INPUT AREA ==================
st.markdown("<div class='input-container'>", unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=True):
    cols = st.columns([8,1])
    with cols[0]:
        user_msg = st.text_input("💬 Type your message...", key="input_box", label_visibility="collapsed")
    with cols[1]:
        send = st.form_submit_button("Send", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ================== HANDLE MESSAGE ==================
if send and user_msg.strip():
    mood, polarity = analyze_sentiment(user_msg)
    suggestion = get_suggestion(mood)
    ai_reply = f"I sense you're feeling **{mood.lower()}** 💭\n\nHere's something for you: {suggestion}"
    save_chat(st.session_state.active_chat, user_msg, ai_reply, mood, polarity, mood, f"User expressed {mood.lower()} mood.")
    st.session_state.scroll_to_bottom = True
    st.rerun()

if st.session_state.get("scroll_to_bottom"):
    st.markdown("<script>document.querySelector('#chat-box').scrollTop = document.querySelector('#chat-box').scrollHeight;</script>", unsafe_allow_html=True)
    st.session_state.scroll_to_bottom = False

st.caption("💚 Developed by Akilzz | Emotion Intelligence Chat Assistant 💚")
