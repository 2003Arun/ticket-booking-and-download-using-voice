import streamlit as st
import speech_recognition as sr
import re
import time
import threading

def listen_for_command():
    """
    Listen for voice command and convert to text
    If microphone is not available, use text input as fallback
    
    Returns:
        str: Recognized voice command text
    """
    # Create placeholders
    placeholder = st.empty()
    input_placeholder = st.empty()
    
    # Only use text input if microphone specifically fails
    if 'mic_failed' in st.session_state and st.session_state.mic_failed:
        placeholder.info("🎤 Voice input unavailable. Please type your command temporarily:")
        text_input = input_placeholder.text_input("Command", key=f"voice_input_{time.time()}", placeholder="Voice recognition will be attempted again on next input...")
        if text_input:
            # Reset mic_failed to try voice recognition again next time
            st.session_state.mic_failed = False
            input_placeholder.empty()
            return text_input
        return None
    
    # Try to use microphone
    try:
        # Initialize recognizer
        r = sr.Recognizer()
        
        with sr.Microphone() as source:
            placeholder.info("Listening... Speak now.")
            
            # Adjust for ambient noise and listen
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            
            placeholder.info("Processing your command...")
            
            # Recognize speech using Google Speech Recognition
            command = r.recognize_google(audio)
            return command
            
    except sr.WaitTimeoutError:
        placeholder.warning("No speech detected. Please try again.")
    except sr.UnknownValueError:
        placeholder.warning("Could not understand audio. Please try again.")
    except sr.RequestError as e:
        placeholder.error(f"Could not request results; {e}")
        # Switch to text input mode temporarily
        st.session_state.mic_failed = True
        placeholder.info("Voice recognition service unavailable. Microphone will be tried again next time.")
        # Don't request text input immediately - will be handled on next call
        return None
    except Exception as e:
        placeholder.error(f"Error: {str(e)}")
        # Switch to text input mode temporarily
        st.session_state.mic_failed = True
        placeholder.info("Microphone unavailable. Voice recognition will be tried again on next input.")
        # Don't request text input immediately - will be handled on next call
        return None
    
    return None

def continuous_listen(callback_function):
    """
    Continuously listen for voice commands and process them
    
    Args:
        callback_function: Function to call when a command is recognized
    """
    def listen_thread():
        while True:
            command = listen_for_command()
            if command:
                callback_function(command)
            time.sleep(0.5)  # Short pause between listening attempts
    
    # Start listening in a separate thread to avoid blocking the UI
    thread = threading.Thread(target=listen_thread)
    thread.daemon = True  # Daemon thread will stop when main program exits
    thread.start()

def extract_ticket_details(command):
    """
    Extract ticket booking details from voice command
    
    Args:
        command (str): Voice command text
        
    Returns:
        dict: Extracted ticket details
    """
    details = {}
    
    # Extract name - improved pattern matching
    name_patterns = [
        r"for\s+([a-zA-Z\s]+?)(?:,|\s+age|\s+from|\s+to|$)",
        r"name\s+(?:is|:)?\s+([a-zA-Z\s]+?)(?:,|\s+age|\s+from|\s+to|$)",
        r"([a-zA-Z\s]+?)\s+age"
    ]
    
    for pattern in name_patterns:
        name_match = re.search(pattern, command, re.IGNORECASE)
        if name_match:
            details["name"] = name_match.group(1).strip()
            break
    
    # Extract age - improved pattern matching
    age_patterns = [
        r"age\s+(\d+)",
        r"(\d+)\s+years?",
        r"(\d+)\s+years?\s+old"
    ]
    
    for pattern in age_patterns:
        age_match = re.search(pattern, command, re.IGNORECASE)
        if age_match:
            try:
                details["age"] = int(age_match.group(1))
                break
            except ValueError:
                pass
    
    # Extract gender
    gender_match = re.search(r"\b(male|female|other)\b", command, re.IGNORECASE)
    if gender_match:
        gender = gender_match.group(1).lower()
        if gender == "male":
            details["gender"] = "Male"
        elif gender == "female":
            details["gender"] = "Female"
        else:
            details["gender"] = "Other"
    
    # Extract source station - improved pattern matching
    source_patterns = [
        r"from\s+([a-zA-Z\s]+?)(?:\s+to|$)",
        r"source\s+(?:is|:)?\s+([a-zA-Z\s]+?)(?:,|\s+to|$)"
    ]
    
    for pattern in source_patterns:
        source_match = re.search(pattern, command, re.IGNORECASE)
        if source_match:
            details["source"] = source_match.group(1).strip()
            break
    
    # Extract destination station - improved pattern matching
    dest_patterns = [
        r"to\s+([a-zA-Z\s]+?)(?:,|\s+with|\s+and|$)",
        r"destination\s+(?:is|:)?\s+([a-zA-Z\s]+?)(?:,|$)"
    ]
    
    for pattern in dest_patterns:
        dest_match = re.search(pattern, command, re.IGNORECASE)
        if dest_match:
            details["destination"] = dest_match.group(1).strip()
            break
    
    return details
