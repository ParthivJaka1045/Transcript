import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

# Page Config
st.set_page_config(page_title="Gujarati Audio Transcriber", layout="centered")

st.title("🎙️ ગુજરાતી ઓડિયો ટ્રાન્સક્રિપ્શન")
st.write("તમારી ઓડિયો ફાઈલ અપલોડ કરો. સિસ્ટમ 3-3 મિનિટના સ્માર્ટ ટુકડા કરીને ગુજરાતીમાં લખી આપશે.")

# File Uploader
uploaded_file = st.file_uploader("ઓડિયો/વીડિયો ફાઈલ પસંદ કરો (MP3, WAV, MP4)", type=["mp3", "wav", "mp4", "m4a"])

if uploaded_file is not None:
    st.audio(uploaded_file, format='audio/mp3')
    
    if st.button("🚀 ટ્રાન્સક્રિપ્શન શરૂ કરો"):
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            status_text.info("ફાઈલ લોડ થઈ રહી છે અને પ્રોસેસ થાય છે... (થોડી વાર લાગશે)")
            
            # Save uploaded file temporarily
            with open("temp_input.mp3", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Load Audio
            sound = AudioSegment.from_file("temp_input.mp3")
            
            status_text.info("વાક્યો અલગ કરવામાં આવી રહ્યા છે (Silence Detection)...")
            
            # Silence based splitting
            chunks = split_on_silence(sound, 
                min_silence_len=700,
                silence_thresh=sound.dBFS-14,
                keep_silence=500
            )
            
            # Setup variables
            r = sr.Recognizer()
            final_text = ""
            current_block_text = ""
            current_block_duration_ms = 0
            target_duration_ms = 3 * 60 * 1000 # 3 Minutes
            part_number = 1
            
            total_chunks = len(chunks)
            
            status_text.info(f"કુલ {total_chunks} વાક્યો મળ્યા છે. ગુજરાતીમાં લખવાનું શરૂ થાય છે...")
            
            # Processing Loop
            for i, chunk in enumerate(chunks):
                # Update Progress Bar
                progress = int((i / total_chunks) * 100)
                progress_bar.progress(progress)
                
                # Export chunk
                chunk_filename = f"temp_chunk_{i}.wav"
                chunk.export(chunk_filename, format="wav")
                
                # Recognize
                try:
                    with sr.AudioFile(chunk_filename) as source:
                        audio_data = r.record(source)
                        text = r.recognize_google(audio_data, language="gu-IN")
                        if text:
                            current_block_text += text + " "
                except:
                    pass # Ignore errors
                
                # Cleanup temp chunk
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)
                
                # Add Duration
                current_block_duration_ms += len(chunk)
                
                # Check for 3 minute cutoff (Smart Cut)
                if current_block_duration_ms >= target_duration_ms:
                    mins = current_block_duration_ms / 1000 / 60
                    header = f"\n\n--- ભાગ {part_number} (લગભગ {mins:.2f} મિનિટ) ---\n"
                    
                    final_text += header + current_block_text
                    
                    # Reset
                    current_block_text = ""
                    current_block_duration_ms = 0
                    part_number += 1
            
            # Process remaining text
            if current_block_text:
                header = f"\n\n--- ભાગ {part_number} (બાકીનો ભાગ) ---\n"
                final_text += header + current_block_text
            
            progress_bar.progress(100)
            status_text.success("✅ ટ્રાન્સક્રિપ્શન પૂરું થઈ ગયું!")
            
            # Display Output
            st.text_area("તમારું લખાણ:", value=final_text, height=400)
            
            # Download Button
            st.download_button(
                label="📥 Text File ડાઉનલોડ કરો",
                data=final_text,
                file_name="gujarati_transcript.txt",
                mime="text/plain"
            )
            
            # Cleanup Input file
            if os.path.exists("temp_input.mp3"):
                os.remove("temp_input.mp3")

        except Exception as e:
            st.error(f"એરર આવી: {e}")