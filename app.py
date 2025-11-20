import streamlit as st
from main import chat, pool, create_session, load_history, save_message, generate_session_name , delete_all_data
from retriever import get_context,add_pdf_or_docx_to_vector_db
from prompts import SYSTEM_PROMPT
from streamlit_mic_recorder import mic_recorder
from speech_to_text import transcribe_audio  # imported our custom function for STT
from text_to_speech import text_to_speech  # imported our custom function for TTS
import tempfile  # for saving audio bytes to temporary file
import os #for deleting temp files



# ---------------- Login ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

if not st.session_state.logged_in: #if user is not logged in
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.radio("Role", ["HR", "Finance", "Other"])
    
    if st.button("Login"):
        if username == "username" and password == "password":
            st.session_state.logged_in = True
            st.session_state.role = role
            st.rerun() #causes the script to rerun from the top
        else:
            st.error("Invalid credentials")
    st.stop() #prevents the below code from appearing if not logged in

role = st.session_state.role

# ---------------- Initialize state ----------------
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "is_new_session" not in st.session_state:
    st.session_state.is_new_session = False
if "mic_counter" not in st.session_state:
    st.session_state.mic_counter = 0

# ---------------- Sidebar ----------------
with st.sidebar:
    st.title("LangChain with Groq API Example")
    st.markdown(f"**Role:** {role}")

    website_url = st.text_input("🌐 Optional: Enter a website URL to include in context").strip() or None
    #################################################### Creating button to add website data to vector db ##############
    if website_url:
     if st.button("➕ Add Website to DB"):
        with st.spinner("Retrieving data from website..."):
            # Call a new function to store website data
            from retriever import add_website_to_db
            add_website_to_db(website_url)
        st.success("Website data added to vector database ✅")
    ####################################################

    # PDF Upload
    st.markdown("### Upload PDF")
    uploaded_files = st.file_uploader("Upload PDFs", type=["pdf", "docx"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            tag = st.radio(                 #lets user select tag for the uploaded pdf
            f"Select tag for {file.name}", 
            options=["HR", "Finance", "Other"], 
            key=f"tag_{file.name}"
            )
            if st.button(f"Upload {file.name}", key=f"upload_{file.name}"):
                file_ext = file.name.split(".")[-1].lower() #get the file extension (pdf or docx)
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                    tmp.write(file.read()) #writes the content of the uploaded pdf to the temp file
                    tmp_path = tmp.name #tmp.name is the path of the temp file
                print(f"\n\n====File.name====\n\n{file.name}\n\n====file.name====\n\n")
                from retriever import add_pdf_or_docx_to_vector_db
                with st.spinner("Adding to vector database...", show_time=True):
                    add_pdf_or_docx_to_vector_db(tmp_path, tag, file.name)
                    st.success(f"{file.name} added to vector database with tag '{tag}'")
                    os.unlink(tmp_path) #delete temp file once its added to vector db 


    # ---------------- Sidebar: Image Upload ----------------
    st.sidebar.markdown("### Upload an image for next chat prompt")
    uploaded_images = st.sidebar.file_uploader(
        "Upload image(s) – max 5 at once", 
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True, 
        key="sidebar_image_upload",
        help="Maximum 5 images allowed (model limit)"
        )

    if uploaded_images:
        if len(uploaded_images) > 5:
            st.sidebar.error("⚠️ Maximum 5 images allowed at once. Extra images will be ignored.")

        uploaded_images = uploaded_images[:5]  # sirf pehle 5 hi rakho
        image_paths = []
        for uploaded_image in uploaded_images:
            image_ext = uploaded_image.name.split(".")[-1].lower() # .jpg ya .png nikala
            temp_image = tempfile.NamedTemporaryFile(delete=False, suffix=f".{image_ext}")
            temp_image.write(uploaded_image.read())
            temp_image.close()
            image_paths.append(temp_image.name)

        # Save list of paths in session state
        st.session_state.uploaded_images = image_paths  # plural
        st.sidebar.success(f"{len(image_paths)} image(s) ready for next chat prompt")



    # ---------------- Session Management Sidebar ----------------


    if st.button("➕ New Chat"):
        # Just mark that a new chat is being started
        st.session_state.session_id = None
        st.session_state.is_new_session = True
        st.rerun()

    if st.button("🗑️ Delete All History"):
        delete_all_data()

    audio = mic_recorder(
    start_prompt="🎙️",
    stop_prompt="⏹️",
    just_once=False,
    use_container_width=True,
    key=f"voice_recorder_{st.session_state.mic_counter}",  # This is the KILLER of loop
    )

    st.markdown("## Chats")
    # st.write(f"session_id: {st.session_state.session_id}")
    # st.write(f"is_new_session: {st.session_state.is_new_session}")

    # Fetch sessions from DB (latest first)
    conn = pool.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, session_name FROM sessions ORDER BY session_id DESC")
    sessions = cursor.fetchall()
    pool.release_conn(conn)

    if not sessions:
        st.write("_No saved chats yet_")
    else:
        for sid, sname in sessions:
            label = sname
            if st.session_state.session_id == sid :
                label = f"📍 {label}"

            if st.button(label, key=f"session_{sid}", use_container_width=True): #so this code is basically mapping each session_id on a button , so we know when what button is click then the value of sessio_id is set to what
                st.session_state.session_id = sid
                st.session_state.is_new_session = False
                st.rerun()

# ---------------- Main Chat Area ----------------
if st.session_state.session_id:  # history will not load if session_id is None
    history = load_history(st.session_state.session_id)
    for msg in history:
        if msg["role"] in ["user", "assistant"]:
            st.chat_message(msg["role"]).write(msg["content"])
            # 🆕 If there’s an audio path for assistant, play it
            if msg["role"] == "assistant" and msg.get("audio_path"):  #Yes — audio_path is the column name in your history table of the database.
                if os.path.exists(msg["audio_path"]):
                    st.audio(msg["audio_path"])

# ---------------- Audio and Chat Input ----------------

prompt = st.chat_input("Say something")
 
if audio:

    # Save audio bytes to a temporary file
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    temp_audio.write(audio["bytes"]) #writes the bytes of the recorded audio to the temp file
    temp_audio_path = temp_audio.name
    temp_audio.close()

   
    with st.spinner("Transcribing..."):
        transcription = transcribe_audio(temp_audio_path) # giving the path of the temp file to our function

    prompt = transcription

    # deletes the temporary file from disk once it has been used
    os.remove(temp_audio_path)



if prompt:
    st.chat_message("user").write(prompt)


    # 🟢 If this is a new chat (not yet saved)
    if st.session_state.session_id is None:
        # create new DB row now
        session_id = create_session("New Chat") #where New Chat is default name
        st.session_state.session_id = session_id
        st.session_state.is_new_session = True
    else:
        session_id = st.session_state.session_id

    save_message(session_id, "user", prompt)

    # Update session name only for first message
    if st.session_state.is_new_session == True:
        session_name = generate_session_name(prompt)
        conn = pool.get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET session_name = ? WHERE session_id = ?",
            (session_name, session_id)
        )
        conn.commit()
        pool.release_conn(conn)
        st.session_state.is_new_session = False

    # ---------------- Check if an image was uploaded in sidebar ----------------
    image_paths = st.session_state.get("uploaded_images")  # list ya None if no image uploaded

    if image_paths:
        from vision import analyze_image
        response = analyze_image(image_paths, user_prompt=prompt)  # ab list jaayegi
        sources = []
        # Saare temp image files delete kar do
        for path in image_paths:
            if os.path.exists(path):
                os.unlink(path)
        if "uploaded_images" in st.session_state:
            del st.session_state.uploaded_images
    else:
        # RAG
        with st.spinner("Retrieving contex..."):
            context, sources = get_context(prompt, role=role)   #✅ Retrieval Step: Finds relevant knowledge
        system = SYSTEM_PROMPT.format(rag_context=context) #✅ Generation prep Step: Injects retrieved context into system prompt
        with st.spinner("Generating response..."):
            response = chat(session_id, system, prompt)        #✅ Generation Step: LLM generates answer using system prompt + user prompt

    # 🗣️ Convert response to audio first
    audio_file_path = text_to_speech(response)

    # 💾 Save both text + audio path
    save_message(session_id, "assistant", response, audio_file_path)

    # 💬 Display text
    st.chat_message("assistant").write(response)

    #show sources if any
    if sources:          #sources is a list eg: ["file1.pdf - page 2", "file2.pdf - page 5"]
        with st.expander("Sources used"):
            for source in sources:  #ka matlab hai list ka har item alag alag iterate hoga.
                st.write(source)

    # 🔊 Play audio
    if audio_file_path and os.path.exists(audio_file_path):
        st.audio(audio_file_path)

    st.session_state.mic_counter += 1  # Increment to force new recorder

