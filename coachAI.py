import streamlit as st
from streamlit_option_menu import option_menu
import google.generativeai as genai  
import time
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
import hashlib 
from st_pages import Page, show_pages # pip install st-pages


# CSS ELEMENTS FOR FONT AND STYLING
with open('./style.css') as f:
    css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Navigation Bar
show_pages(
   [   Page("milkyway.py", "Home", "🏠"),
       Page("AI_Sports_Analytics.py", "Sports Analytics", "🏠"),
       Page("coachAI.py", "Coach AI", ":question:"),
       Page("playmaker_ai.py", "Playmaker AI", ":frame_with_picture:")
   ])

# TRANSLATE FUNCTION

translate_client = translate.Client()

def translate_text(text, target_language):
    # Using Google Cloud Translation to translate text
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

# GET ANSWER FUNCTION
def get_answer(question, detail_level):
    genai.configure(api_key='AIzaSyAqftCh8yiBK4IOVFycZIWGSwvH-3umuHA')  
    model = genai.GenerativeModel('models/gemini-pro') 
    detailed_prompt = f"{question} [Detail level: {detail_level}]"
    answer = model.generate_content(detailed_prompt)

    try:
        answer_text = answer.result['candidates'][0]['content']['parts'][0]['text']
    except (AttributeError, KeyError):
        answer_text = answer.text  # Fallback method

    return answer_text

# DOWNLOAD BUTTON FUNCTION
def create_download_button(content, key):
    content_to_download = content.encode()
    st.download_button(label="Download AI-generated content",
                       data=content_to_download,
                       file_name="ai_generated_content.txt",
                       mime="text/plain",
                       key=key)

# INITIALIZE BIGQUERY CLIENT
def initialize_bigquery_client():
    try:
        service_account_key_path = '/home/brent_piper/final-project-milkyway/milkeywayStreamlit/secrets.json'
        credentials = service_account.Credentials.from_service_account_file(
            service_account_key_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(credentials=credentials, project=credentials.project_id)
    except FileNotFoundError:
        print("Warning: Google Cloud service account key file not found.")
        return None

# USER MANAGEMENT FUNCTIONS
def create_user(username, password):
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        bq_client = initialize_bigquery_client()
        query = f"""
        INSERT INTO  `coach-ai-420314.coachAI_DS.LoginTable` (username, password)
        VALUES ('{username}', '{hashed_password}')
        """
        bq_client.query(query).result()
        return True
    except Exception as e:
        st.error(f"Sign Up Failed: {e}")
        return False

def verify_user(username, password):
    try:
        bq_client = initialize_bigquery_client()
        query = f"""
            SELECT password
            FROM  `coach-ai-420314.coachAI_DS.LoginTable`
            WHERE username = @username
        """
        query_params = [bigquery.ScalarQueryParameter("username", "STRING", username)]
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = bq_client.query(query, job_config=job_config)

        results = query_job.result()
        first_row = next(results, None)

        if first_row is None:
            st.error("No account exists with the given username. Please sign up.")
            return False
        elif hashlib.sha256(password.encode()).hexdigest() == first_row.password:
            return True
        else:
            st.error("Incorrect password. Please try again.")
            return False
    except Exception as e:
        st.error(f"Login failed due to an unexpected error: {e}")
        return False

def login_or_sign_up():
    if not st.session_state.get('logged_in', False):
        action = st.sidebar.selectbox("Choose an action:", ["Login", "Sign Up"], key="action_select")
        input_username = st.sidebar.text_input("Username", key="input_username")
        password = st.sidebar.text_input("Password", type="password", key="password")

        if action == "Sign Up":
            confirm_password = st.sidebar.text_input("Confirm Password", type="password", key="confirm_password")
            if st.sidebar.button("Sign Up", key="signup_button"):
                if password == confirm_password:
                    if create_user(input_username, password):
                        st.success("Signup successful! Please login.")
                        st.balloons()
                        return  # Exit the function after successful sign-up
                    else:
                        st.error("Failed to sign up. Please try again.")
                else:
                    st.error("Passwords do not match.")
        elif action == "Login" and st.sidebar.button("Login", key="login_button"):
            if verify_user(input_username, password):
                st.session_state['logged_in_username'] = input_username
                st.session_state['logged_in'] = True
                st.rerun()

    if st.session_state.get('logged_in', False):
        st.markdown(f"### Welcome Back To Coach AI, {st.session_state.get('logged_in_username', 'Guest')}!")
        st.write("You are now logged into your Coach AI Account.")
        if st.button("Logout", key="logout_button"):
            # Clear specific keys to avoid partial state retention
            keys_to_clear = ['logged_in_username', 'logged_in']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_rerun()
def main():

    # client = bigquery.Client('carloshernandeztechx2024')
    # query = ("SELECT * FROM carloshernandeztechx2024.AI_Analytics.Basketball ORDER BY Day_Time DESC LIMIT 1000")
    # df = client.query(query).to_dataframe()            # Display the DataFrame
    # st.write("### Basketball Team Statistics")
    # st.write(df)

    st.sidebar.title("FANHUB")

    if not st.session_state.get('logged_in', False):
        selected = option_menu(
            menu_title="MilkyWay Sports",
            options=["Main Menu", "Playmaker AI", "AI Sports Analytics", "Coach AI", "Sports Article Summarizer"],
            icons=["house", "info-circle", "envelope", "robot"],
            key="option_menu"
        )
        login_or_sign_up()

    if st.session_state.get('logged_in', False):
        if 'selected' not in st.session_state:
            st.session_state['selected'] = "Coach AI"

        selected = st.session_state['selected']

        st.markdown(f"### Welcome Back To Coach AI, {st.session_state.get('logged_in_username', 'Guest')}!")
        st.write("You are now logged into your Coach AI Account.")
        if st.button("Logout", key="logout_button"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]

        if selected == "Coach AI":
            st.title("Welcome to Coach AI!")
            st.write("Ask any sports-related question and get AI-generated answers!")
            detail_level = st.slider("Select the detail level of the response:", 1, 5, 3)
            want_translation = st.checkbox('Do you want to translate your response to another language?', value=False)
            language = st.selectbox("Translate response to:", options=['en', 'es', 'fr', 'de', 'zh', 'ar'],
                                    format_func=lambda x: {'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German', 'zh': 'Chinese', 'ar': 'Arabic'}[x])
            question = st.text_input("Enter your sports-related question:")
            
            if st.button("Get Answer", key="get_answer_button"):
                if question:
                    with st.container():
                        answer = get_answer(question, detail_level)  # Ensure 'answer' is set
                        st.subheader("Answer")
                        st.write(answer)
                        create_download_button(answer, key="original")
                        if want_translation:
                            translated_answer = translate_text(answer, language)
                            formatted_answer = "#### Translated Answer\n" + translated_answer.replace("* ", "\n- ")
                            st.subheader("Translated Answer")
                            st.write(translated_answer)
                            create_download_button(translated_answer, key="translated")
                else:
                    st.warning("Please enter a question.")

if __name__ == "__main__":
    main()
