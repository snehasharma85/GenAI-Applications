# frontend/app.py

import streamlit as st
import requests

st.title("🛍️ AI Shopping Assistant")

query = st.text_input("What are you looking for?")

if st.button("Find Products"):
    if query:
        with st.spinner("Thinking..."):
            response = requests.post(
                "http://localhost:8000/recommend",
                json={"query": query}
            )
            if response.status_code == 200:
                st.markdown(response.json().get("response", "No products found."))
            else:
                st.error("Failed to get a response from the assistant.")
