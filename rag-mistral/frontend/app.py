import streamlit as st
import requests

st.title("📄 PDF Chatbot with Mistral")

# Upload section
st.header("Upload PDFs")
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    if st.button("Upload Document"):
        with st.spinner("Uploading file..."):
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            response = requests.post("http://localhost:8000/upload", files=files)

            if response.ok:
                st.success(response.json()["message"])
            else:
                st.error(f"Failed to upload: {response.text}")


# Question/Answer section
st.header("Ask a question about your documents")

query = st.text_input("Your question:")

if st.button("Ask"):
    if not query.strip():
        st.error("Please enter a question first!")
    else:
        with st.spinner("Thinking..."):
            response = requests.post("http://localhost:8000/ask", data={"query": query})

            if response.ok:
                answer = response.json()["answer"]
                sources = response.json()["sources"]

                st.success(answer)
                st.info(f"Answer based on: {', '.join(set(sources))}")
            else:
                st.error(f"Error: {response.status_code} - {response.text}")

# Clear database button
if st.button("Clear all uploaded documents"):
    response = requests.delete("http://localhost:8000/clear")
    if response.ok:
        st.success("All documents cleared. System reset.")
    else:
        st.error(f"Failed to clear: {response.text}")
