from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


def get_context(user_message):
    """Takes user message as input and returns retrieved context from the PDF."""

        
    # loader = PyPDFLoader(pdf_path) # Uncomment the line below if you want to load documents again
    # docs = loader.load()

    # Embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

    # Chroma vector store
    vector_store = Chroma(
        collection_name="rdr2",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",
    )

    # vector_store.add_documents(docs) # Uncomment if you want to add documents again

    # Use retriever
    retriever = vector_store.as_retriever()
    results = retriever.invoke(user_message)

    # Return best match (first result)
    if results:
        return results
    else:
        return "No relevant information found."
