import streamlit as st
import pandas as pd
from Ai_agnet_realestate import create_real_estate_agent

# === Load CSV data ===
@st.cache_data
def load_properties():
    return pd.read_csv("fake_real_estate_data.csv")  # or properties.csv if you renamed it

properties_df = load_properties()

# === Streamlit setup ===
st.set_page_config(page_title="🏡 وكيل العقارات", page_icon="🏡")
st.title("🤖 وكيل العقارات الذكي")

# === Initialize AI Agent ===
if 'agent' not in st.session_state:
    st.session_state.agent = create_real_estate_agent(properties_df, dialect="egyptian")

if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": st.session_state.agent.get_greeting()}]

# === Display chat messages ===
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === Chat input ===
user_input = st.chat_input("💬 اكتب طلبك هنا...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Process user message through your AI agent
    response = st.session_state.agent.process_input(user_input)

    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.markdown(response)

# === Sidebar: Dialect switcher ===
dialect = st.sidebar.selectbox("اختر اللهجة", st.session_state.agent.get_available_dialects())
if dialect != st.session_state.agent.current_dialect:
    confirmation = st.session_state.agent.set_dialect(dialect)
    st.sidebar.success(confirmation)
