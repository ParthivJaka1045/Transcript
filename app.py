import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

# Page Config
st.set_page_config(page_title="Gujarati Transcriber Pro", layout="centered")

st.title("🎙️ ગુજરાતી ઓડિયો/વીડિયો ટ્રાન્સક્રિપ્શન")
st.write("ઓડિયો કે વીડિયો અપલોડ કરો. સિસ્ટમ સ્માર્ટ ટુકડા કરીને ગુજરાતીમાં લખી આપશે.")

# 1. File Uploader (Video & Audio both)
uploaded_file = st.file_uploader("ફાઈલ પસંદ કરો", type=["mp3", "wav", "mp4", "m4a", "mkv", "avi"])

if uploaded_file is not None:
    # ફાઈલની માહિતી બતાવો
    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}
    st.write(file_details)

    # જો ઓડિયો હોય તો પ્લેયર બતાવો, વીડિયો હોય તો વીડિયો પ્લેયર
    if "video" in uploaded_file.type:
        st.video(uploaded_file)
    else:
        st.audio(uploaded_file)
    
    if st.button("🚀 ટ્રાન્સક્રિપ્શન શરૂ કરો"):
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            status_text.info("ફાઈલ લોડ થઈ રહી છે... (મોટી ફાઈલ હોય તો ધીરજ રાખજો)")
            
            # 2. Save file with correct extension (Video support fix)
            file_extension = uploaded_file.name.split(".")[-1]
            temp_filename = f"temp_input.{file_extension}"
            
            with open(temp_filename, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Load Audio (Pydub handles MP4/MKV automatically via FFmpeg)
            sound = AudioSegment.from_file(temp_filename)
            
            # Sound Info
            total_duration_sec = len(sound) / 1000
            st.write(f"👉 કુલ લંબાઈ: {total_duration_sec/60:.2f} મિનિટ")

            status_text.info("ઓડિયોના નાના ટુકડા કરવામાં આવી રહ્યા છે...")
            
            # 3. Hybrid Splitting Logic (Fix for Empty Text)
            # પહેલા Silence થી ટ્રાય કરીએ, પણ જો ટુકડા મોટા હોય તો તેને નાના કરીએ
            
            # સેટિંગ: દરેક ટુકડો 60 સેકન્ડથી મોટો ન હોવો જોઈએ (Google API લિમિટ માટે)
            chunk_length_ms = 60 * 1000 
            chunks = []
            
            # સળંગ 60-60 સેકન્ડના ટુકડા કરીએ (આ સૌથી સેફ રીત છે જેથી કોઈ લાઈન મિસ ન થાય)
            for i in range(0, len(sound), chunk_length_ms):
                chunks.append(sound[i : i + chunk_length_ms])
            
            total_chunks = len(chunks)
            status_text.info(f"પ્રોસેસિંગ માટે {total_chunks} ભાગ કર્યા. હવે ગૂગલ પર મોકલી રહ્યા છીએ...")
            
            # Setup variables
            r = sr.Recognizer()
            final_text = ""
            current_3min_block = ""
            current_3min_duration = 0
            part_number = 1
            target_duration = 3 * 60 * 1000 # 3 Minutes Output Limit
            
            # Processing Loop
            for i, chunk in enumerate(chunks):
                # Update Progress
                progress = int((i / total_chunks) * 100)
                progress_bar.progress(progress)
                
                # Export temp chunk
                chunk_filename = f"temp_chunk_{i}.wav"
                chunk.export(chunk_filename, format="wav")
                
                # Recognize
                try:
                    with sr.AudioFile(chunk_filename) as source:
                        audio_data = r.record(source)
                        # ગુજરાતી ભાષા માટે
                        text = r.recognize_google(audio_data, language="gu-IN")
                        
                        if text:
                            current_3min_block += text + " "
                        else:
                            current_3min_block += " [અવાજ સ્પષ્ટ નથી] "
                            
                except sr.UnknownValueError:
                    # જો કઈ સંભળાયું ન હોય
                    pass
                except sr.RequestError:
                    st.error("ઇન્ટરનેટ કનેક્શન એરર!")
                    break
                except Exception as e:
                    print(e)
                
                # Cleanup
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)
                
                # Logic for 3 Minute Grouping in Output
                current_3min_duration += len(chunk)
                
                if current_3min_duration >= target_duration:
                    mins = current_3min_duration / 1000 / 60
                    header = f"\n\n--- ભાગ {part_number} (લગભગ {mins:.2f} મિનિટ પૂરી) ---\n"
                    final_text += header + current_3min_block
                    
                    # Reset
                    current_3min_block = ""
                    current_3min_duration = 0
                    part_number += 1
            
            # બાકી રહેલો ભાગ
            if current_3min_block:
                header = f"\n\n--- ભાગ {part_number} (બાકીનો ભાગ) ---\n"
                final_text += header + current_3min_block
            
            progress_bar.progress(100)
            status_text.success("✅ ટ્રાન્સક્રિપ્શન સફળ!")
            
            # Display Output
            st.subheader("તમારું લખાણ:")
            st.text_area("પરિણામ", value=final_text, height=400)
            
            # Download
            st.download_button(
                label="📥 ગુજરાતી ફાઈલ ડાઉનલોડ કરો",
                data=final_text,
                file_name="gujarati_transcript.txt",
                mime="text/plain"
            )
            
            # Cleanup Main File
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        except Exception as e:
            st.error(f"મોટી એરર આવી: {e}")
            st.warning("જો 'FileNotFoundError' કે 'ffmpeg' ની એરર હોય, તો ખાતરી કરો કે તમારા PC માં FFmpeg ઇન્સ્ટોલ છે.")