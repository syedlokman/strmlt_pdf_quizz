import streamlit as st
import subprocess
import google.generativeai as genai
import json
import base64
import pathlib
import pprint
import requests
import mimetypes
import re
import pandas as pd

def getSubtitle(url, language='English'):
    if language == "English":
        srt_command = f'yttool --language en --subtitles {url}'  # English playlist
    else:
        srt_command = f'yttool --language asr --subtitles {url}'  # for CampusX

    try:
        result = subprocess.run(srt_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subtitle = result.stdout
        word_count = len(subtitle.split())
        return {"subtitle": subtitle, "wordcount": word_count}
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e.stderr}")
        return {"subtitle": "", "wordcount": 0}


# Function to validate the form inputs
def validate_form(genaiAPI, language, postType, url):
    if not genaiAPI:
        st.error("genaiAPI is required")
        return False
    if language == "Unknown":
        st.error("Please select a valid language")
        return False
    if not postType:
        st.error("postType is required")
        return False
    if not url:
        st.error("Video URL is required")
        return False
    # Additional validation logic can be added here
    return True

st.sidebar.title("Video Processing Form")

# Create a form
with st.sidebar.form(key='video_form'):
    # Streamlit app code
    genaiAPI = st.text_input('genaiAPI', placeholder='Paste genaiAPI here')
    language = st.selectbox("Video Language:", ("English", "Bangla", "Hindi", "Other"), placeholder="Language")
    postType = st.selectbox("postType?", ("NoOutline", "WithOutline", "TipsNTricks", "Code"), placeholder="postType")
    outline = st.text_area('outline', placeholder='outline')
    model_name = st.text_input('gemini model:', "gemini-1.5-pro-latest")
    url = st.text_input('Video URL', placeholder='Paste the URL here')

    # Submit button
    submit_button = st.form_submit_button(label='Submit')


# Handle form submission
with st.sidebar:
    if submit_button:
        if validate_form(genaiAPI, language, postType, url):
            st.success("Form submitted successfully!")
            # Downstream processing
        else:
            st.error("Form submission failed due to validation errors.")
            st.stop()
    
    if not submit_button:
        st.warning('Please submit the form.')
        st.stop()
    
    # Use regular expression to remove timestamps
    outline_cleaned = re.sub(r"\d+:\d+ - ", "", outline)
    print(outline_cleaned)
    video = getSubtitle(url, language)
    st.sidebar.write("WordCount: ", video['wordcount'])

    st.write("Processing the form data...")
    st.write(f"genaiAPI: {genaiAPI}")
    st.write(f"Language: {language}")
    st.write(f"postType: {postType}")
    st.write(f"Outline: {outline_cleaned}")
    st.write(f"Model Name: {model_name}")
    st.write(f"Video URL: {url}")

    lecture = video['subtitle']

    if postType == "Code":
        msg= f"""write the python code discussed in the lecture with great explanation. here is the lecture:```
        {lecture}``` """
    elif postType == "WithOutline":
        msg = f"""make a detailed blog with multisections including examples out of the given lecture in English following this outline:```
        {outline_cleaned} ```
        Lecture:``` {lecture} ```
        Detailed Blog Post Including Examples: """
    elif postType == "TipsNTricks":
        msg = f"""You are very good in understanding Hindi. make a list of all the tips, tricks, or hacks in English from this LECTURE. Do not say that you can't process Hindi. : ```
        {lecture} ``` """
    else:
        msg = f"""make a blog with multisections out of this in English:```
        {lecture} ``` """

    expander = st.expander("User Prompt")
    expander.write(msg)




genai.configure(api_key=genaiAPI)



# Set up the model
generation_config = {"temperature": 1, "top_p": 0.95, "top_k": 0,
                     "max_output_tokens": 8192,
                    #  "max_output_tokens": 2048,
                     }
safety_settings = [{ "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" },
  { "category": "HARM_CATEGORY_HATE_SPEECH",  "threshold": "BLOCK_NONE"  },
  { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE" },
  { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE" }, ]

system_instruction = ""

model = genai.GenerativeModel(
    model_name= model_name,
    generation_config=generation_config,
    # system_instruction=system_instruction,
    safety_settings=safety_settings)


convo = model.start_chat(history=[])
convo.send_message(msg)
response = convo.last
response.text