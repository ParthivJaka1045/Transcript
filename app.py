import streamlit as st
import whisper
import os
import time

# Page Config (Title in English)
st.set_page_config(page_title="Gujarati Transcriber Pro", layout="centered")

# UI Title & Instructions in English
st.title("🎙️ High Quality Gujarati Transcription")
st.write("Upload your Audio/Video file. The system will use OpenAI Whisper to generate a **Pure Gujarati** transcript with high accuracy.")

# --- 1. Model Loading (Cache) ---
@st.cache_resource
def load_model():
    # Loading 'medium' model for best results
    return whisper.load_model("medium")

st.info("Loading AI Model... Please wait.")
model = load_model()
st.success("AI Model is Ready!")

# --- 2. File Uploader (English Label) ---
uploaded_file = st.file_uploader("Choose an Audio/Video file (MP3, WAV, MP4)", type=["mp3", "wav", "mp4", "m4a", "mkv"])

if uploaded_file is not None:
    # Show Player
    if "video" in uploaded_file.type:
        st.video(uploaded_file)
    else:
        st.audio(uploaded_file)

    # Button in English
    if st.button("🚀 Start Transcription"):
        
        status_box = st.empty()
        
        try:
            # Save file temporarily
            file_extension = uploaded_file.name.split(".")[-1]
            temp_filename = f"temp_input.{file_extension}"
            
            with open(temp_filename, "wb") as f:
                f.write(uploaded_file.getbuffer())

            status_box.info("⏳ Transcription in progress... This may take a few minutes depending on file size.")
            
            # --- WHISPER TRANSCRIPTION (Gujarati) ---
            # language="gu" ensures the output is Gujarati
            result = model.transcribe(temp_filename, language="gu", fp16=False)
            
            status_box.success("✅ Processing complete! Formatting text...")

            # --- 3. Output Formatting (3 Minute Blocks) ---
            final_text = ""
            current_block_text = ""
            part_number = 1
            block_limit = 3 * 60 # 3 Minutes in seconds
            next_cutoff = block_limit

            # Loop through segments
            for segment in result["segments"]:
                end_time = segment["end"]
                text = segment["text"]

                # Check if the sentence falls within the current 3-minute limit
                if end_time < next_cutoff:
                    current_block_text += text + " "
                else:
                    # Calculate start and end minutes for the Header
                    end_min = (next_cutoff / 60)
                    start_min = end_min - 3
                    
                    # New Header Format: "0 to 3 Minutes"
                    header = f"\n\n--- {start_min:.0f} to {end_min:.0f} Minutes ---\n"
                    final_text += header + current_block_text
                    
                    # Start new block
                    current_block_text = text + " "
                    part_number += 1
                    next_cutoff += block_limit

            # Add the remaining text (Last part)
            if current_block_text:
                start_min = (next_cutoff - block_limit) / 60
                header = f"\n\n--- {start_min:.0f} Minutes onwards ---\n"
                final_text += header + current_block_text

            # --- Display & Download ---
            st.subheader("Transcript Output:")
            st.text_area("Generated Text", value=final_text, height=400)
            
            # Download Button in English
            st.download_button(
                label="📥 Download Transcript (.txt)",
                data=final_text,
                file_name="transcript.txt",
                mime="text/plain"
            )

            # Cleanup
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        except Exception as e:
            st.error(f"An error occurred: {e}")