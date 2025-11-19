from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

def get_context(user_message, role):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

    vector_store = Chroma(
        collection_name="rdr2",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",
    )

    retriever = vector_store.as_retriever(
        search_kwargs={"filter": {"tag": role}, "k": 5}  # top 5 results  #this line is used to  ferform filtering in RAG based on tag (role) , this line matches the pdf tag with user login role to give him results from relevent docs
    )

    results = retriever.get_relevant_documents(user_message) #stores list of doc objects in results : each doc object has page_content and metadata attribute

    if results: 
        # Build context
        context_text = "\n\n".join([doc.page_content for doc in results]) #Matlab: "results" list me har doc object ke liye, uska page_content uthao."

        # Build sources: sirf filename + page
        sources = set()                         #set is used to avoid duplicate entries, as set automatically handles removes duplicates
        for doc in results:
            # PDF path se sirf filename nikalo
            pdf_name = doc.metadata.get("filename", "Unknown") #filename key m pdf ka name hai , jo hmny manually store krwaya tha jab pdf ko vector db m add kr rhy thy
            page_no = doc.metadata.get("page_label", "Unknown")  #page_label key m page number hai , jo langchain khud store krta hai jab pdf ko vector db m add kr rhy thy
            sources.add(f"{pdf_name} — page no: {page_no}")
        # agar list chahiye to:
        sources = list(sources)

        return context_text, sources
    else:
        return "No relevant context found in the database.", []


###########################----------Website Scrapping Code-----------###############################################
from langchain_community.document_loaders import RecursiveUrlLoader #to extract websites data from link
from langchain_text_splitters import RecursiveCharacterTextSplitter  #required for chunking the data

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

###########################----------Add uploaded PDF/DOCX(converted to pdf) with Tag Code-----------###############################################
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from docx2pdf import convert #to convert docx to pdf on windows

def add_pdf_or_docx_to_vector_db(file_path, tag, filename):
    """
    Uploads a PDF or Word file (docx) to Chroma vector DB.
    - If Word, convert to PDF first (preserves page numbers)
    - Then load PDF using PyPDFLoader
    - Adds metadata: filename + tag
    """
    # Initialize embeddings and vector store
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    vector_store = Chroma(
        collection_name="rdr2",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",
    )

    file_ext = filename.split(".")[-1].lower()

    # If Word, convert to PDF first using docx2pdf
    if file_ext == "docx":
        pdf_path = file_path.replace(".docx", ".pdf")
        convert(file_path, pdf_path)
    else:
        pdf_path = file_path  # already a PDF
    
    
    # Load PDF
    loader = PyPDFLoader(pdf_path)
    docs = loader.load() #stores a list of doc objects in docs, each doc object has page_content as key in metadata attribute

    # Add metadata
    for doc in docs:
        print(f"\n\n====SAMPLE_DOC====\n\n{doc}\n\n====SAMPLE_DOC====\n\n") #debugging purpose, to see the structure of doc object
        doc.metadata["filename"] = filename   #filename matadata m nhi hota , so khud say add karna padta hai
        doc.metadata["tag"] = tag   #tag matadata m nhi hota , so khud say add karna padta hai


    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunked_docs = splitter.split_documents(docs)

    # Add to vector DB and persist
    vector_store.add_documents(chunked_docs)