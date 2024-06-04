import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import os

genai.configure(api_key="AIzaSyA4C9EnTtEXfzVhkIW_H--qcLgDLWYULl8")

def upload_to_gemini(path, mime_type=None):
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def save_uploaded_file(uploadedfile):
    # Save uploaded file to a temporary directory
    with open(os.path.join("tempDir", uploadedfile.name), "wb") as f:
        f.write(uploadedfile.getbuffer())
    return os.path.join("tempDir", uploadedfile.name)

def pdftoimage(pdf):
  doc = fitz.open(pdf)  # Open the PDF document
  images = [] # List to store images

  for page in doc: # Iterate through the pages and convert them to images
      pix = page.get_pixmap()  # Render page to an image
      img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
      images.append(img)  # Store the PIL image in the list

  # Calculate the total height and width for the final image
  total_height = sum(img.height for img in images)
  max_width = max(img.width for img in images)

  # Create a new blank image with the calculated dimensions
  final_image = Image.new("RGB", (max_width, total_height))

  # Paste each page image into the final image
  current_y = 0
  for img in images:
      final_image.paste(img, (0, current_y))
      current_y += img.height

  # Save the final concatenated image
  final_image.save("combined_image.png")

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE",
  },
]

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro-latest",
  safety_settings=safety_settings,
  generation_config=generation_config,
)

# Configure the title and sidebar of the Streamlit app
st.title('PDF to QuizMaker')

# Define the main function for handling the form and the PDF conversion
def main():
    # Create a form for PDF upload
    with st.form(key='pdf_form'):
        pdf_file = st.file_uploader("**Upload PDF**", type=['pdf'])
        gemini_api_key = st.text_input('**Gemini API Key** (Get the api key from [Google AiStudio](https://aistudio.google.com/app/apikey) )', placeholder='Paste genaiAPI here')
        submit_button = st.form_submit_button(label='Submit')

    # Handle form submission
    if submit_button:
        if pdf_file is not None and gemini_api_key:
            # Save the uploaded PDF to a temporary file
            pdf_path = save_uploaded_file(pdf_file)
            image = pdftoimage(pdf_path)

            # Initialize progress bar
            progress_bar = st.progress(10)
            progress_text = st.empty()
            progress_text.text(f"Processing ...")
            
            # Send images to Gemini API and get the generated content
            image_animal3 = upload_to_gemini("./combined_image.png", mime_type="image/png")

            # Display the generated content
            chat_session = model.start_chat(
              history=[
                {
                  "role": "user",
                  "parts": [
                    image_animal3,
                  ],
                },
              ]
            )

            extractiveSummary = chat_session.send_message(""" You can read images and understand them to make a list of key concept and then create a detailed extractive summarization of those concepts from the given image as if you are learning it in details 
            """)

            # Update progress bar and text
            progress = 33
            progress_bar.progress(progress)
            progress_text.text(f"Key Concepts Extraction Done. Preparing Quizzes...")

            # Display the Markdown content
            with st.expander("Key Concepts", expanded=False):
              extractiveSummary.text

            quizQs = chat_session.send_message(f"""
              create a quiz paper containing 10 MCQ, 10 True/False, 5 Short questions, and 5 Critical Thinking questions from the concepts described in the image. give more emphasize on the following concepts:```{extractiveSummary.text}```. Quiz Paper:""")

            # Update progress bar and text
            progress = 66
            progress_bar.progress(progress)
            progress_text.text(f"Quizz Done. Answer in progress...")

            # Display the Markdown content
            with st.expander("Quizzes", expanded=False):
              quizQs.text

            answerQs = chat_session.send_message(f"""
              return answers of these questions with detailed explanation. Questions: ```{quizQs}```""")

            # Update progress bar and text
            progress = 100
            progress_bar.progress(progress)
            progress_text.text(f"Answered. Please Check.")

            # Display the Markdown content
            with st.expander("Answers", expanded=False):
              answerQs.text

        else:
            st.error("Please upload a PDF and provide a Gemini API key.")

if __name__ == '__main__':
    # Create tempDir if it doesn't exist
    if not os.path.exists('tempDir'):
        os.makedirs('tempDir')
    main()
