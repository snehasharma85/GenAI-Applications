import streamlit as st
import requests

st.set_page_config(page_title="Incident Search", layout="centered")

st.title("🔍 Incident Search (RAG UI)")

query = st.text_input("Search for an incident, error or RCA:")

if not query:
    st.info("Enter a search term above to begin.")
else:
    try:
        response = requests.post(
            "http://localhost:8000/search",
            json={"query": query}
        )

        st.write("🧠 Backend response status:", response.status_code)

        if response.status_code == 200:
            results = response.json()["results"]
            if not results:
                st.warning("No matching results found.")
            else:
                st.success(f"Top {len(results)} similar records found")

                for i, res in enumerate(results):
                    st.subheader(f"Result {i+1}")
                    st.write(res["document"])
                    st.json(res["metadata"])
                    st.markdown("---")
        else:
            st.error(f"Search failed. Status code: {response.status_code}")
            st.text(response.text)
    except Exception as e:
        st.error("Could not connect to backend.")
        st.exception(e)
