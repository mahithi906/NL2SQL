# langchain_project/app/frontend.py

import streamlit as st
import requests

API_URL = "http://localhost:8000/api/nl2sql"

st.set_page_config(page_title="NL2SQL Chatbot", page_icon="🤖")

st.title(" NL2SQL Chatbot")
st.write("Ask any question about the AdventureWorks database in plain English.")

question = st.text_input("Your question:")

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking..."):
            res = requests.post(API_URL, json={"question": question}).json()

        st.subheader(" Final Answer")
        st.success(res["answer"])

        if res.get("sql"):
            st.subheader(" SQL Query")
            st.code(res["sql"], language="sql")

        if res.get("rows"):
            st.subheader(" Query Results")
            st.dataframe(res["rows"])

        st.subheader(" Debug Flow")
        for step in res["flow"]:
            st.text(step)
