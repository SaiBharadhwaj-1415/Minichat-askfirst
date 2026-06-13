import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Mini AI Chat",
    layout="wide"
)

st.title("Mini AI Chat")

# Sidebar
st.sidebar.title("Chats")

if st.sidebar.button("➕ New Chat"):

    count = len(
        requests.get(f"{BASE_URL}/threads").json()
    ) + 1

    requests.post(
        f"{BASE_URL}/threads",
        json={
            "title": f"Chat {count}"
        }
    )

threads = requests.get(
    f"{BASE_URL}/threads"
).json()

if len(threads) == 0:
    st.info("Create a new chat.")
    st.stop()

thread_names = [
    f"{t['id']} - {t['title']}"
    for t in threads
]

selected = st.sidebar.radio(
    "Select Thread",
    thread_names
)

thread_id = int(selected.split(" - ")[0])

messages = requests.get(
    f"{BASE_URL}/threads/{thread_id}/messages"
).json()

for msg in messages:

    if msg["role"] == "user":
        st.chat_message("user").write(
            msg["content"]
        )
    else:
        st.chat_message("assistant").write(
            msg["content"]
        )

user_input = st.chat_input(
    "Type your message..."
)

if user_input:

    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "thread_id": thread_id,
            "message": user_input
        }
    )

    st.rerun()