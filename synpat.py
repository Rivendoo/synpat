import streamlit as st
import requests
import re
import json

# Hårdkodad CassidyAI API-nyckel och Assistant ID
API_KEY = "mitPxZU_ier-oAVubaLv1SscDTpJNASPvwdr7rrznBs"
ASSISTANT_ID = "clt5k8v7002bnmc0lhlfmu2i8"

# API-endpoints
CREATE_THREAD_URL = "https://app.cassidyai.com/api/assistants/thread/create"
SEND_MESSAGE_URL = "https://app.cassidyai.com/api/assistants/message/create"

# Lösenord för autentisering
PASSWORD = "patientupplevelse"

# Initialisera session state för autentisering, tråd ID, meddelandehistorik och referenser
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None

if 'messages' not in st.session_state:
    # Lägg till det första meddelandet från assistenten
    st.session_state.messages = [
        {"role": "assistant", "content": "Hej, jag är en fiktiv patient. Ställ en fråga?"}
    ]

if 'all_references' not in st.session_state:
    st.session_state.all_references = []  # Lista av dicts med 'n', 'name', 'description'

# Anpassad CSS för att förbättra UI, inklusive Roboto-font
def local_css():
    st.markdown(
        """
        <style>
        /* Importera Roboto-fonten */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@100&display=swap');

        /* Färgpalett */
        .first-color { 
            background: #ffffff; 
        }
        .second-color { 
            background: #ffe9e3; 
        }
        .third-color { 
            background: #ffffff; 
        }
        .fourth-color { 
            background: #7c73e6; 
        }

        /* Allmän styling */
        body, .stApp, [class*="css"] {
            background-color: #ffffff !important; /* Ändrad till #ffffff */
            font-family: 'Roboto', sans-serif; /* Uppdaterad till Roboto */
            color: #262626; /* All text till #262626 */
        }
        /* Avatarer */
        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
        }
        .user-avatar {
            /* Ändrat från bild till färgad cirkel */
            background-color: #7c73e6; /* .fourth-color */
            width: 40px;
            height: 40px;
            border-radius: 50%;
        }
        .assistant-avatar {
            /* Assistentens avatarbild */
            content: url("https://i.imgur.com/8Km9tLL.png");
            width: 40px;
            height: 40px;
            border-radius: 50%;
        }
        /* Chatbubblor */
        .chat-container {
            display: flex;
            flex-direction: column;
            max-height: 70vh;
            overflow-y: auto;
            padding: 20px;
            background-color: #ffffff; /* Bakgrund för chatten */
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .message-row {
            display: flex;
            align-items: flex-end;
            gap: 10px;
            margin-bottom: 20px; /* Ökat mellanrum mellan meddelanden */
        }
        .user-bubble {
            align-self: flex-end;
            background-color: #f0f2f6; /* .second-color */
            color: #262626; /* Textfärg */
            padding: 10px 15px;
            border-radius: 20px;
            max-width: 60%; /* Begränsa maxbredden */
            word-wrap: break-word;
        }
        .assistant-bubble {
            align-self: flex-start;
            background-color: #ffe9e3; /* .third-color */
            color: #262626; /* Textfärg */
            padding: 10px 15px;
            border-radius: 20px;
            max-width: 60%; /* Begränsa maxbredden */
            word-wrap: break-word;
        }
        /* Referenslistan */
        .references {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        .references h3 {
            margin-bottom: 10px;
            color: #262626; /* Textfärg */
        }
        .references ul {
            list-style-type: decimal;
            padding-left: 20px;
        }
        .references li {
            margin-bottom: 5px;
            color: #262626; /* Textfärg */
        }
        /* Typing Indicator */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 5px;
            margin-top: 10px; /* Lägg till avstånd ovanför indikatoren */
        }
        .typing-indicator .dot {
            width: 8px;
            height: 8px;
            background-color: #7c73e6; /* .fourth-color */
            border-radius: 50%;
            animation: typing 1.4s infinite both;
        }
        .typing-indicator .dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-indicator .dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes typing {
            0% {
                transform: translateY(0);
                opacity: 0.7;
            }
            50% {
                transform: translateY(-8px);
                opacity: 1;
            }
            100% {
                transform: translateY(0);
                opacity: 0.7;
            }
        }
        /* Scrollbar styling */
        .chat-container::-webkit-scrollbar {
            width: 8px;
        }
        .chat-container::-webkit-scrollbar-track {
            background: #f1f1f1; 
        }
        .chat-container::-webkit-scrollbar-thumb {
            background: #888; 
            border-radius: 4px;
        }
        .chat-container::-webkit-scrollbar-thumb:hover {
            background: #555; 
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Funktion för autentisering
def authenticate():
    st.title("Inloggning")
    with st.form("login_form"):
        password_input = st.text_input("Ange lösenord:", type="password")
        submit = st.form_submit_button("Logga in")
        if submit:
            if password_input == PASSWORD:
                st.session_state.authenticated = True
            else:
                st.error("Fel lösenord. Försök igen.")

# Funktion för att skapa en ny tråd
def create_thread():
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "assistant_id": ASSISTANT_ID
    }
    try:
        response = requests.post(CREATE_THREAD_URL, headers=headers, json=data)
        response.raise_for_status()
        json_response = response.json()
        thread_id = json_response.get("thread_id")
        if not thread_id:
            st.error("Tråd ID saknas i API-svaret.")
        return thread_id
    except requests.exceptions.RequestException as e:
        st.error(f"Fel vid skapande av tråd: {e}")
        return None

# Funktion för att skicka ett meddelande och bearbeta referenser
def send_message(thread_id, message):
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "thread_id": thread_id,
        "message": message  # Skickar meddelandet som en sträng
    }
    try:
        response = requests.post(SEND_MESSAGE_URL, headers=headers, json=data)
        response.raise_for_status()
        json_response = response.json()

        # Hämta assistentens svar från rätt nyckel
        assistant_response = json_response.get("content") or json_response.get("content_with_references")
        references = json_response.get("references", [])

        if not assistant_response:
            st.error("Assistentens svar saknas i API-svaret.")
            return "Ursäkta, något gick fel.", []

        # Processa referenser och uppdatera markeringarna
        updated_content, new_references = process_references(assistant_response, references)

        return updated_content, new_references
    except requests.exceptions.RequestException as e:
        st.error(f"Fel vid skickande av meddelande: {e}")
        return "Ursäkta, något gick fel.", []

# Funktion för att processa referenser och uppdatera markeringar
def process_references(content_with_refs, references):
    """
    Ersätt [[n]] i content_with_refs med globala referensnummer
    och uppdatera den globala referenslistan.
    """
    # Hitta alla [[n]] marker
    markers = re.findall(r'\[\[(\d+)\]\]', content_with_refs)

    updated_content = content_with_refs

    for marker in markers:
        index = int(marker)  # 0-baserad index
        if index < len(references):
            ref = references[index]
            ref_key = ref['url']  # Unik identifierare

            # Kontrollera om referensen redan finns
            existing_ref = next((item for item in st.session_state.all_references if item['url'] == ref_key), None)
            if existing_ref:
                global_n = existing_ref['n']
            else:
                global_n = len(st.session_state.all_references) + 1
                st.session_state.all_references.append({
                    "n": global_n,
                    "name": ref['name'],
                    "description": extract_description(ref['name'], ref['url'])
                })

            # Ersätt [[n]] med [[global_n]]
            updated_content = updated_content.replace(f'[[{marker}]]', f'[[{global_n}]]')

    return updated_content, []

# Funktion för att extrahera beskrivning från referensnamn
def extract_description(name, url):
    """
    Generera en beskrivning baserat på referensens namn och URL.
    Detta kan anpassas för bättre beskrivningar.
    """
    # Här kan du lägga till logik för att generera mer beskrivande texter
    return f"{name}."

# Funktion för att omvandla messages till en sträng
def format_chat_history(messages):
    """
    Konvertera listan av messages till en sträng för prompten.
    """
    history = ""
    for msg in messages:
        if msg["role"] == "user":
            history += f"Human: {msg['content']}\n"
        else:
            history += f"AI: {msg['content']}\n"
    return history.strip()

# Funktion för huvudinnehållet i appen
def main_app():
    local_css()

    # Ställ in sidan med en titel och avatar
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <h3 style="margin:0; color: #262626;">Syntetisk cancerpatient</h3> <!-- All text färgad #262626 -->
        </div>
        """, unsafe_allow_html=True)

    # Initialisera tråd om ingen tråd ID finns
    if st.session_state.thread_id is None:
        with st.spinner("Skapar chatttråd..."):
            thread_id = create_thread()
            if thread_id:
                st.session_state.thread_id = thread_id
            else:
                st.stop()

    # Skapa en container för chatten
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                    <div class="message-row">
                        <div class="user-avatar"></div>
                        <div class="user-bubble">{msg["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="message-row">
                        <img src="https://i.imgur.com/8Km9tLL.png" alt="Assistant Avatar" class="avatar assistant-avatar">
                        <div class="assistant-bubble">{msg["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # Skapa en placeholder för typing indicator placerad under chat-container
    typing_placeholder = st.empty()

    # Ta emot användarens inmatning
    user_input = st.chat_input("Skriv ett meddelande...")

    if user_input:
        # Lägg till användarens meddelande till historiken
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container:
            st.markdown(f"""
                <div class="message-row">
                    <div class="user-avatar"></div>
                    <div class="user-bubble">{user_input}</div>
                </div>
                """, unsafe_allow_html=True)

        # Visa typing indicator
        with typing_placeholder.container():
            st.markdown("""
                <div class="typing-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
                """, unsafe_allow_html=True)

        # Skicka meddelandet till API:et och få assistentens svar
        assistant_reply, _ = send_message(st.session_state.thread_id, user_input)

        # Ta bort typing indicator
        typing_placeholder.empty()

        # Lägg till assistentens svar till historiken
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
        with chat_container:
            st.markdown(f"""
                <div class="message-row">
                    <img src="https://i.imgur.com/8Km9tLL.png" alt="Assistant Avatar" class="avatar assistant-avatar">
                    <div class="assistant-bubble">{assistant_reply}</div>
                </div>
                """, unsafe_allow_html=True)

    # Visa referenslistan om det finns några referenser
    if st.session_state.all_references:
        st.markdown("""
            <div class="references">
                <h3>Referenser:</h3>
                <ul>
        """, unsafe_allow_html=True)
        for ref in st.session_state.all_references:
            st.markdown(f"<li><strong>{ref['n']}. {ref['name']}</strong>. {ref['description']}</li>", unsafe_allow_html=True)
        st.markdown("</ul></div>", unsafe_allow_html=True)

# Konditionell Rendering baserat på autentiseringsstatus
if not st.session_state.authenticated:
    authenticate()
else:
    main_app()
