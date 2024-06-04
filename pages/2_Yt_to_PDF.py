import streamlit as st
import cv2
from pytube import YouTube
import os
from moviepy.editor import VideoFileClip, vfx
from img2pdf import convert

def convert_to_1fps_video(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_1fps_filename = f'1fps_{os.path.basename(video_path)}'

    if not os.path.exists(video_1fps_filename):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use MPEG-4 Part 2 codec
        out = cv2.VideoWriter(video_1fps_filename, fourcc, 1, (width, height))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        progress_bar = st.progress(0, text="Converting video to 1 FPS...")

        frame_counter = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_counter % fps == 0:
                out.write(frame)

            frame_counter += 1
            progress_bar.progress(frame_counter / total_frames)

        cap.release()
        out.release()
        progress_bar.empty()
        st.success("Video converted to 1 FPS successfully")

    return video_1fps_filename

# Step 1: Download a YouTube video from the given link
def download_video(url):
    yt = YouTube(url)
    video_filename = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().default_filename

    if not os.path.exists(video_filename):
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        video.download(output_path='.', filename=video_filename, max_retries=10)
    return video_filename


def compress_video_to_2x(input_path):
    output = f'compressed_{input_path}'

    if not os.path.exists(output):
        # Load the video file
        video = VideoFileClip(input_path)
        # Speed up the video to 2x
        video_2x = video.fx(vfx.speedx, 10)
        # Save the sped-up video
        video_2x.write_videofile(output)
    return output


# def convert_to_1fps_video(video_path):
#     cap = cv2.VideoCapture(video_path)
#     fps = int(cap.get(cv2.CAP_PROP_FPS))
#     width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

#     video_1fps_filename = f'1fps_{os.path.basename(video_path)}'

#     if not os.path.exists(video_1fps_filename):
#         out = cv2.VideoWriter(video_1fps_filename, cv2.VideoWriter_fourcc(*'mp4v'), 1, (width, height))

#         total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#         progress_bar = st.progress(0, text="Converting video to 1 FPS...")
#         for i in range(total_frames):
#             ret, frame = cap.read()
#             if not ret:
#                 break
#             if i % fps == 0:
#                 out.write(frame)
#             progress_bar.progress(i / total_frames)

#         # st.success("Video converted to 1 FPS successfully")
#         cap.release()
#         out.release()
#         return video_1fps_filename

#     return video_1fps_filename


@st.cache_data
def remove_duplicate_frames(video_path, output_path, pdf_path):
    cap = cv2.VideoCapture(video_path)
    height, width, _ = (int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                        int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        3)
    
    # Resize the frames for faster processing
    resize_width = 480
    resize_height = int(height * (resize_width / width))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use MPEG-4 Part 2 codec
    out = cv2.VideoWriter(output_path, fourcc, cap.get(cv2.CAP_PROP_FPS), (width, height))
    
    prev_frame = None
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    progress_bar_video = st.progress(0, text="Processing video and removing duplicates...")
    unique_frames = []
    
    for i in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize the frame for faster processing
        frame_resized = cv2.resize(frame, (resize_width, resize_height))
        
        gray_frame = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        
        if prev_frame is None:
            out.write(frame)  # Write the original frame to the output video
            prev_frame = gray_frame
            unique_frames.append(frame)
        else:
            # Calculate histogram difference
            hist_prev = cv2.calcHist([prev_frame], [0], None, [256], [0, 256])
            hist_curr = cv2.calcHist([gray_frame], [0], None, [256], [0, 256])
            hist_diff = cv2.compareHist(hist_prev, hist_curr, cv2.HISTCMP_CHISQR)
            
            # Set a threshold for histogram difference
            hist_threshold = 6000
            
            if hist_diff > hist_threshold:
                out.write(frame)  # Write the original frame to the output video
                prev_frame = gray_frame
                unique_frames.append(frame)
            
        progress_bar_video.progress((i + 1) / total_frames)
    progress_bar_video.empty()

    cap.release()
    out.release()
    
    st.success(f"Unique Frame Detected: {len(unique_frames)}")

    # Compress unique frames using JPEG compression
    compressed_frames = []
    for img in unique_frames:
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]  # Set JPEG quality to 80 (0-100)
        _, encoded_img = cv2.imencode('.jpg', img, encode_param)
        compressed_frames.append(encoded_img.tobytes())
    
    # Generate PDF from compressed frames
    progress_bar_pdf = st.progress(0)
    with open(pdf_path, "wb") as f:
        f.write(convert(compressed_frames))
        for i in range(len(compressed_frames)):
            progress_bar_pdf.progress((i + 1) / len(compressed_frames))
    progress_bar_pdf.empty()
            
    # with st.spinner("Saving PDF..."):
    #     # Generate PDF from unique frames
    #     with open(pdf_path, "wb") as f:
    #         f.write(convert([cv2.imencode(".png", img)[1].tobytes() for img in unique_frames]))

    st.success(f"Output video saved as {output_path}")
    st.success(f"PDF with {len(unique_frames)} pages saved as {pdf_path}")

@st.cache_data
def download_files(output_path, pdf_path):
    st.markdown("### Download Files")
    
    video_data = None
    pdf_data = None
    
    with open(output_path, "rb") as video_file:
        video_data = video_file.read()
    
    with open(pdf_path, "rb") as pdf_file:
        pdf_data = pdf_file.read()
    
    return {'video': video_data, 'pdf': pdf_data}

def app():
    st.title("Video Deduplication")
    

    with st.form(key='video_form'):
        url = st.text_input("Enter YouTube video URL")
        submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        if not url.startswith('http'):
            st.warning("Please enter a valid YouTube URL")
            return

        with st.spinner("Downloading video..."):
            video_path = download_video(url)
            st.success("Video downloaded successfully")

        with st.spinner("Converting video to 1 FPS..."):
            video_1fps_filename = convert_to_1fps_video(video_path)
            st.success("Video converted to 1fps successfully")

        with st.spinner("Compressing video..."):
            compressed_video_path = compress_video_to_2x(video_1fps_filename)
            st.success("Video compressed successfully")

        with st.spinner("Processing video..."):
            output_path = f"output_{os.path.basename(video_path)}"
            pdf_path = f"{os.path.splitext(output_path)[0]}.pdf"
            remove_duplicate_frames(compressed_video_path, output_path, pdf_path)

            files = download_files(output_path, pdf_path)

            st.download_button(
                label="Download Output Video",
                data=files['video'],
                file_name="output_video.mp4",
                mime="video/mp4"
            )
            
            st.download_button(
                label="Download PDF",
                data=files['pdf'],
                file_name="document.pdf",
                mime="application/pdf"
            )


if __name__ == "__main__":
    app()