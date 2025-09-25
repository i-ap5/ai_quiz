import streamlit as st
import os
import logging
import json
import google.generativeai as genai
import time

# Setup basic logging to help debug in the terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==============================================================================
# UNIVERSAL AI-NATIVE PARSER (The Correct Approach)
# ==============================================================================

def configure_ai():
    """Configures the Gemini AI with the API key from Streamlit secrets."""
    try:
        if "GOOGLE_API_KEY" in st.secrets and st.secrets["GOOGLE_API_KEY"]:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            return True
        else:
            st.error("Error: GOOGLE_API_KEY not found in Streamlit secrets.")
            st.info("Please create a file named `.streamlit/secrets.toml` and add your key: `GOOGLE_API_KEY = 'YOUR_API_KEY_HERE'`")
            return False
    except Exception as e:
        st.error(f"AI Configuration Error: {e}")
        logging.error(f"AI Configuration Error: {e}")
        return False

def parse_quiz_file_with_ai(file_path):
    """
    The universal parser. It uploads the entire file to the Gemini 1.5 Pro model
    and asks it to return a structured JSON of questions using its native
    document understanding capabilities.
    """
    if not configure_ai():
        return []

    try:
        st.info("Keedam AI is analyzing your document. This may take a few moments...")
        logging.info(f"Uploading file to Gemini: {file_path}")
        
        # Upload the file to the Gemini API
        quiz_file = genai.upload_file(path=file_path)

        # Configure the model
        model = genai.GenerativeModel('gemini-2.5-flash')

        # This is the "Master Prompt" that tells the AI how to behave
        prompt = """
        You are an expert data extraction system with native multimodal understanding. You will be given a file (PDF) that contains a quiz. Your only task is to analyze the entire document's layout, formatting, and text to extract all the questions and return them as a single, valid JSON array.

        Each JSON object in the array must have exactly three keys:
        1. "question": A string containing the full, complete text of the question.
        2. "options": An array of strings, where each string is a possible option.
        3. "answer": A string containing the full and exact text of the correct option.

        You must intelligently determine the correct answer for each question by looking for one of three patterns in the source document:
        - The correct option's text is formatted in **bold**.
        - An answer is explicitly given after the options, like "Ans. a".
        - The answers are listed in a table or key at the end of the document.

        CRITICAL RULES:
        - The value for the "answer" key MUST be an exact match to one of the strings in the "options" array.
        - Clean the output text: Do not include question numbers (like "1.") or option letters (like "a)") in the final JSON strings.
        - If a question is incomplete, malformed, or you cannot confidently determine the correct answer, you MUST skip it entirely.
        - Your final output must ONLY be the JSON array, with no other text, comments, or markdown formatting like ```json.
        """

        logging.info("Sending prompt and file to the AI model...")
        
        # Send the prompt and the file object to the model
        response = model.generate_content([prompt, quiz_file])
        
        # Clean the AI's response to get a pure JSON string
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        
        # Convert the JSON string into a Python list
        questions = json.loads(json_text)
        
        logging.info(f"AI Parser successfully extracted {len(questions)} questions.")
        st.success(f"AI analysis complete! Found {len(questions)} questions.")
        return questions
        
    except Exception as e:
        st.error("An error occurred while the AI was analyzing the file.")
        st.error(f"Details: {e}")
        logging.error(f"AI Parsing Failed: {e}")
        # In case of an error, try to show the raw response for debugging
        if 'response' in locals() and hasattr(response, 'text'):
            st.code(response.text, language="text")
        return []

# = an=============================================================================
# STREAMLIT APPLICATION UI
# ==============================================================================
def main():
    st.set_page_config(page_title="AI Quiz Generator", page_icon="✈️", layout="centered")
    st.title("✈️ Keedam AI Quiz Generator")

    if 'state' not in st.session_state:
        st.session_state.state = 'initial'
        st.session_state.questions = []
        st.session_state.current_question = 0
        st.session_state.user_answers = {}

    if st.session_state.state == 'initial':
        st.info("Upload any supported PDF quiz file. The AI will do the rest!")
        
        uploaded_file = st.file_uploader("Upload your Quiz File", type=["pdf"])

        if uploaded_file:
            # Save the uploaded file to a temporary location
            temp_dir = "uploads"
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Call the single, universal AI parser
            st.session_state.questions = parse_quiz_file_with_ai(temp_file_path)
            
            if st.session_state.questions:
                st.session_state.state = 'quiz_started'
                st.rerun()
            else:
                st.error("The AI could not find any valid questions in this file. Please check the document or try another one.")
        return

    # The rest of the UI logic is stable and does not need to change
    if st.session_state.state == 'finished':
        score = sum(1 for i, q in enumerate(st.session_state.questions) if st.session_state.user_answers.get(i) == q['answer'])
        
        st.success(f"## 🎯 Quiz Complete!")
        st.write(f"### Your Final Score: {score} out of {len(st.session_state.questions)}")
        with st.expander("Review Your Answers"):
             for i, q in enumerate(st.session_state.questions):
                user_answer = st.session_state.user_answers.get(i, "Not Answered")
                correct_answer = q['answer']
                if user_answer == correct_answer:
                    st.markdown(f"**Q{i+1}: {q['question']}**\n\n✅ Your answer: `{user_answer}` (Correct)")
                else:
                    st.markdown(f"**Q{i+1}: {q['question']}**\n\n❌ Your answer: `{user_answer}`\n\nCorrect answer: `{correct_answer}`")
                st.markdown("---")
        if st.button("Take a New Quiz"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        return

    if st.session_state.state in ['quiz_started', 'show_feedback']:
        q_index = st.session_state.current_question
        q_data = st.session_state.questions[q_index]

        def jump_to_question():
            selected_q_text = st.session_state.question_jumper
            # new_index = int(selected_q_text.split(" ")) - 1
            new_index = int(selected_q_text.split(" ")[1]) - 1

            st.session_state.current_question = new_index
            st.session_state.state = 'quiz_started'

        st.selectbox("Skip to question:", options=[f"Question {i+1}" for i in range(len(st.session_state.questions))],
            index=st.session_state.current_question, on_change=jump_to_question, key='question_jumper')
        st.markdown("---")

        st.subheader(f"Question {q_index + 1} of {len(st.session_state.questions)}")
        st.markdown(f"<p style='font-size: 20px; font-weight: 500;'>{q_data['question']}</p>", unsafe_allow_html=True)
        
        valid_options = [opt for opt in q_data["options"] if opt]
        
        if st.session_state.state == 'quiz_started':
            with st.form(key=f"form_{q_index}"):
                previous_answer = st.session_state.user_answers.get(q_index)
                previous_answer_index = valid_options.index(previous_answer) if previous_answer in valid_options else 0
                user_choice = st.radio("Choose your answer:", options=valid_options, key=f"radio_{q_index}", index=previous_answer_index)
                submitted = st.form_submit_button("Check Answer")
                if submitted:
                    st.session_state.user_answers[q_index] = user_choice
                    st.session_state.state = 'show_feedback'
                    st.rerun()
        
        elif st.session_state.state == 'show_feedback':
            last_answer = st.session_state.user_answers.get(q_index, "")
            try: default_index = valid_options.index(last_answer)
            except (ValueError, IndexError): default_index = 0
            
            st.radio("Your Answer:", options=valid_options, index=default_index, disabled=True)
            
            correct_answer = q_data['answer']
            if last_answer == correct_answer:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Incorrect! The correct answer was: **{correct_answer}**")
            
            
            is_last_question = (q_index + 1 == len(st.session_state.questions))
            button_text = "Finish Quiz" if is_last_question else "Next Question ->"
            if st.button(button_text,use_container_width=True ):
                if not is_last_question:
                    st.session_state.current_question += 1
                    st.session_state.state = 'quiz_started'
                else:
                    st.session_state.state = 'finished'
                st.rerun()

if __name__ == "__main__":
    main()