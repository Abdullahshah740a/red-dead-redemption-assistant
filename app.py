import streamlit as st
from main import chat  # Import the chat function from main.py
from retriever import get_context  # Import the get_context function from retriever.py
from prompts import SYSTEM_PROMPT  # Import the system prompt from prompts.py
import time
from main import load_history  # Import load_history to display past messages
from main import save_message  # Import save_message to save user messages

with st.sidebar:
    st.title("LangChain with Groq API Example")
    st.markdown("**RDR2 GuideBot**")

history = load_history()

for msg in history:
    if msg["role"] in ["user", "assistant"]:  # system ko skip kar do
        st.chat_message(msg["role"]).write(msg["content"])


if prompt := st.chat_input("Say something"):
    save_message("user", prompt)
    st.chat_message("user").write(prompt)
    
    
    with st.spinner("Retrieving context...", show_time=True):
        context = get_context(prompt) # Retrieve context based on user prompt
    
    system_message = SYSTEM_PROMPT.format(rag_context=context)
    
    with st.spinner("Generating response...", show_time=True):
        response = chat(system_message, prompt) # Generate response from chat function
    save_message("assistant", response)
    st.chat_message("assistant").write(response)

