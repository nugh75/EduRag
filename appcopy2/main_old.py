# main.py

import streamlit as st

def main():
    st.title("Edubot Interface")

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select a page", ["Home", "PDF Processing", "Query"])

    if page == "Home":
        st.write("""
        ## Welcome to Edubot Interface
        Use the sidebar to navigate between:
        - **PDF Processing**: Create or load a FAISS index from PDFs.
        - **Query**: Interact with a chatbot using the FAISS index.
        """)
    elif page == "PDF Processing":
        from pdf_processing_page import pdf_processing_page
        pdf_processing_page()
    elif page == "Query":
        from app.query_page import query_page
        query_page()

if __name__ == "__main__":
    main()
