from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv(override=True)

LLAMA = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model=os.getenv("GROQ_API_MODEL"),
    temperature=os.getenv("GROQ_API_TEMPRATURE"),
    )