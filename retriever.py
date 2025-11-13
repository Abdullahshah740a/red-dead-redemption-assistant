from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

def get_context(user_message):
    """
    Retrieves context either from the PDF (already stored) 
    or from a new website if URL is provided.
    """

        
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
    retriever = vector_store.as_retriever()       #Core of RAG , Converts the vector store into a "retriever" object that can perform search operations.
    results = retriever.invoke(user_message)      #Core of RAG , Retrieves similar documents/context from the vector database

    # Return best match (first result)
    if results:
        return results
    else:
        return "No relevant information found."

###########################----------Website Scrapping Code-----------###############################################
from langchain_community.document_loaders import RecursiveUrlLoader #to extract websites data from link
from langchain.text_splitter import RecursiveCharacterTextSplitter  #required for chunking the data

def add_website_to_db(website_url):
    """
    Loads a website, splits into chunks, and stores in vector DB.
    """
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    vector_store = Chroma(
        collection_name="rdr2",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",
    )

    # --- STEP that is doing the website content retrievaland storign it in vector databse so llm can use that info if needed : Add website data if a URL is given
    if website_url not in str(vector_store.get()):    # ✅ Check if this website's content is already in the vector database — prevents reloading same URL again
        loader = RecursiveUrlLoader(website_url, max_depth=1) #scraps data from website
        docs = loader.load()
        
        # Chunking
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunked_docs = splitter.split_documents(docs)

        vector_store.add_documents(chunked_docs)
