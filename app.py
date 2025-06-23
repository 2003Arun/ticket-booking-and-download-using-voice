import streamlit as st
import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta
import time
import re
import io
import base64
from fpdf import FPDF

from voice_recognition import listen_for_command, extract_ticket_details
from ticket_operations import (
    book_ticket, 
    modify_ticket, 
    cancel_ticket, 
    get_all_tickets, 
    get_ticket_by_id,
    get_tickets_by_name
)
from stations import get_station_list

# Initialize session state variables if they don't exist
if 'tickets' not in st.session_state:
    st.session_state.tickets = []  # Store ticket data
if 'current_operation' not in st.session_state:
    st.session_state.current_operation = None
if 'listening' not in st.session_state:
    st.session_state.listening = False
if 'voice_message' not in st.session_state:
    st.session_state.voice_message = ""
if 'voice_command' not in st.session_state:
    st.session_state.voice_command = None
if 'ticket_details' not in st.session_state:
    st.session_state.ticket_details = {}
if 'selected_ticket_id' not in st.session_state:
    st.session_state.selected_ticket_id = None
if 'booking_step' not in st.session_state:
    st.session_state.booking_step = None
if 'user_voice_input' not in st.session_state:
    st.session_state.user_voice_input = None
if 'first_run' not in st.session_state:
    st.session_state.first_run = True
if 'last_prompt' not in st.session_state:
    st.session_state.last_prompt = None
if 'prompt_time' not in st.session_state:
    st.session_state.prompt_time = time.time()
if 'show_success' not in st.session_state:
    st.session_state.show_success = False
if 'success_message' not in st.session_state:
    st.session_state.success_message = ""
if 'mic_failed' not in st.session_state:
    # Attempt to use microphone first, only fallback to text if needed
    st.session_state.mic_failed = False  # Try to use speech recognition by default

# Page configuration
st.set_page_config(
    page_title="Smart public Transportation System",
    page_icon="🚆",
    layout="wide"
)

# Main title
st.title("Smart public Transportation System")
st.subheader("Voice-Activated for Visually Impaired Users")

# Information for users
st.markdown("""
### This application is fully voice-controlled
- The system will automatically listen for your voice commands
- No buttons need to be pressed
- Speak clearly to interact with the system

### Available commands:
- Say "Book a ticket" to create a new booking
- Say "Modify a ticket" to change an existing ticket
- Say "Cancel a ticket" to remove a booking
- Say "View tickets" to hear all your bookings
- Say "Help" at any time for assistance
""")

# Status and message display
status_container = st.empty()
message_container = st.empty()

# Fallback visual output for voice responses
voice_output_container = st.container()
with voice_output_container:
    voice_output = st.empty()

# Helper functions
def create_ticket_pdf(ticket):
    """
    Create a downloadable PDF from ticket data
    
    Args:
        ticket (dict): The ticket data
        
    Returns:
        str: Base64 encoded PDF data for download
    """
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font("Arial", "B", 16)
    
    # Title
    pdf.cell(190, 10, "RAILWAY TICKET", 1, 1, "C")
    pdf.ln(10)
    
    # Ticket details
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "Ticket ID:", 0, 0)
    pdf.set_font("Arial", "", 12)
    pdf.cell(140, 10, ticket["id"], 0, 1)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "Passenger Name:", 0, 0)
    pdf.set_font("Arial", "", 12)
    pdf.cell(140, 10, ticket["name"], 0, 1)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "Age:", 0, 0)
    pdf.set_font("Arial", "", 12)
    pdf.cell(140, 10, str(ticket["age"]), 0, 1)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "Gender:", 0, 0)
    pdf.set_font("Arial", "", 12)
    pdf.cell(140, 10, ticket["gender"], 0, 1)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "From:", 0, 0)
    pdf.set_font("Arial", "", 12)
    pdf.cell(140, 10, ticket["source"], 0, 1)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "To:", 0, 0)
    pdf.set_font("Arial", "", 12)
    pdf.cell(140, 10, ticket["destination"], 0, 1)
    
    # Add travel date if it exists
    if "travel_date" in ticket:
        try:
            date_obj = datetime.strptime(ticket["travel_date"], "%Y-%m-%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
            
            pdf.set_font("Arial", "B", 12)
            pdf.cell(50, 10, "Travel Date:", 0, 0)
            pdf.set_font("Arial", "", 12)
            pdf.cell(140, 10, formatted_date, 0, 1)
        except:
            pass
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "Booking Time:", 0, 0)
    pdf.set_font("Arial", "", 12)
    pdf.cell(140, 10, ticket["booking_time"], 0, 1)
    
    # Generate footer
    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(190, 10, "Thank you for choosing our Railway Service!", 0, 1, "C")
    
    # Generate PDF as bytes
    pdf_bytes = pdf.output(dest="S").encode("latin1")
    
    # Convert to base64 for download link
    b64 = base64.b64encode(pdf_bytes).decode("latin1")
    return b64

def get_ticket_download_link(ticket):
    """
    Generate a download link for the ticket
    
    Args:
        ticket (dict): The ticket data
        
    Returns:
        str: HTML download link
    """
    # Create PDF and encode to base64
    b64_pdf = create_ticket_pdf(ticket)
    
    # Generate accessible, highly prominent download link with enhanced styling
    href = f'''
    <div style="text-align: center; margin: 20px 0;">
        <a href="data:application/pdf;base64,{b64_pdf}" 
           download="ticket_{ticket['id']}.pdf" 
           style="display:inline-block; 
                  background-color:#0066cc; 
                  color:white; 
                  padding:15px 30px; 
                  text-decoration:none; 
                  font-weight:bold; 
                  border-radius:10px; 
                  font-size:1.5em; 
                  margin:15px 0;
                  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                  transition: all 0.3s ease;">
            📄 DOWNLOAD TICKET PDF
        </a>
        <p style="margin-top:10px; font-size:1em; color:#333; font-weight:bold;">Ticket ID: {ticket['id']} • Passenger: {ticket['name']}</p>
        <p style="margin-top:5px; font-size:0.9em; color:#555;">Click the blue button above to download your ticket as a PDF file</p>
    </div>
    '''
    return href

def display_text_as_voice(text):
    """
    Display text on screen and attempt to speak it using TTS
    """
    # Always show visual output as fallback
    voice_output.info(f"🔊 System says: {text}")
    
    try:
        # Import and initialize TTS engine
        import pyttsx3
        
        # Initialize the TTS engine
        engine = pyttsx3.init()
        
        # Set properties (optional)
        engine.setProperty('rate', 150)    # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume (0 to 1)
        
        # Convert text to speech
        engine.say(text)
        
        # Wait for speech to complete
        engine.runAndWait()
    except Exception as e:
        # If TTS fails, we already have visual output as fallback
        pass

# Main Operations
def process_main_menu():
    """Handle the main menu state"""
    if st.session_state.first_run:
        display_text_as_voice("Welcome to the Railway Ticket Reservation System. This system is fully controlled by your voice. Say 'Book a ticket', 'Modify a ticket', 'Cancel a ticket', or 'View tickets'.")
        st.session_state.first_run = False
    
    status_container.info("Listening for main command...")
    command = listen_for_command()
    
    if command:
        message_container.success(f"I heard: {command}")
        
        # Process the command
        if "book" in command.lower() or "new" in command.lower() or "ticket" in command.lower():
            st.session_state.current_operation = "book"
            display_text_as_voice("Starting new ticket booking process. Please tell me your name.")
            st.session_state.booking_step = "name"
        
        elif "modify" in command.lower() or "edit" in command.lower() or "change" in command.lower():
            st.session_state.current_operation = "modify"
            if st.session_state.tickets:
                display_text_as_voice("You have the following tickets. You can say the ID number or passenger name of the ticket you want to modify.")
                for idx, ticket in enumerate(st.session_state.tickets):
                    ticket_info = f"Ticket {idx+1}, ID {ticket['id']}, {ticket['name']}, from {ticket['source']} to {ticket['destination']}"
                    display_text_as_voice(ticket_info)
                
                # Initialize the modification process
                st.session_state.modify_step = "select_ticket"
            else:
                display_text_as_voice("You don't have any tickets to modify. Say 'Book a ticket' to create a new booking.")
                st.session_state.current_operation = None
        
        elif "cancel" in command.lower() or "delete" in command.lower() or "remove" in command.lower():
            st.session_state.current_operation = "cancel"
            if st.session_state.tickets:
                display_text_as_voice("You have the following tickets. Please say the ID number or passenger name of the ticket you want to cancel.")
                for idx, ticket in enumerate(st.session_state.tickets):
                    ticket_info = f"Ticket {idx+1}, ID {ticket['id']}, {ticket['name']}, from {ticket['source']} to {ticket['destination']}"
                    display_text_as_voice(ticket_info)
                
                # Initialize the cancellation process
                st.session_state.cancel_step = "select_ticket"
            else:
                display_text_as_voice("You don't have any tickets to cancel. Say 'Book a ticket' to create a new booking.")
                st.session_state.current_operation = None
        
        elif "view" in command.lower() or "show" in command.lower() or "list" in command.lower() or "all" in command.lower():
            st.session_state.current_operation = "view"
            st.session_state.view_step = "display_options"
            display_text_as_voice("How would you like to view your tickets? Say 'All tickets' to see all, say a name to search by passenger, or say a ticket ID to see a specific ticket.")
            
        elif "find" in command.lower() or "search" in command.lower() or "my tickets" in command.lower() or "my name" in command.lower():
            st.session_state.current_operation = "view"
            st.session_state.view_step = "ask_name"
            display_text_as_voice("Please say the passenger name to search for.")
            
        elif "ticket id" in command.lower() or "find id" in command.lower() or "search id" in command.lower() or "lookup id" in command.lower() or "ticket number" in command.lower():
            st.session_state.current_operation = "view"
            st.session_state.view_step = "ask_id"
            display_text_as_voice("Please say the ticket ID you want to look up.")
        
        elif "help" in command.lower():
            display_text_as_voice("Here are the available commands: Say 'Book a ticket' to create a new booking. Say 'Modify a ticket' followed by a name or ID to change an existing ticket. Say 'Cancel a ticket' followed by a name or ID to remove a booking. Say 'View tickets' to see all your bookings. Say 'Ticket ID' followed by your ticket number to look up a specific ticket. Say 'Find tickets' followed by a name to search for tickets by passenger name.")
        
        else:
            display_text_as_voice("Sorry, I didn't understand that command. Please try again.")
    
    else:
        display_text_as_voice("I'm listening for your command. Say 'Book a ticket', 'Modify a ticket' followed by a name or ID, 'Cancel a ticket' followed by a name or ID, 'View tickets', 'Look up ticket ID', or 'Search by name'. You can also say 'Help' for a list of all commands.")

def process_booking():
    """Handle the ticket booking process"""
    status_container.info(f"Booking step: {st.session_state.booking_step}")
    
    if st.session_state.booking_step == "name":
        status_container.info("Listening for name...")
        name = listen_for_command()
        
        if name:
            message_container.success(f"I heard: {name}")
            st.session_state.ticket_details['name'] = name
            display_text_as_voice(f"Name recorded as {name}. Now, please say your age.")
            st.session_state.booking_step = "age"
        else:
            display_text_as_voice("I couldn't hear your name. Please say your full name.")
    
    elif st.session_state.booking_step == "age":
        status_container.info("Listening for age...")
        age_input = listen_for_command()
        
        if age_input:
            message_container.success(f"I heard: {age_input}")
            try:
                # Extract age from input
                age_match = re.search(r'\b(\d+)\b', age_input)
                if age_match:
                    age = int(age_match.group(1))
                    if 1 <= age <= 120:
                        st.session_state.ticket_details['age'] = age
                        display_text_as_voice(f"Age recorded as {age}. Now, please say your gender: Male, Female, or Other.")
                        st.session_state.booking_step = "gender"
                    else:
                        display_text_as_voice("Age must be between 1 and 120. Please try again.")
                else:
                    display_text_as_voice("I couldn't understand your age. Please say a number clearly.")
            except ValueError:
                display_text_as_voice("I couldn't understand your age. Please say a number clearly.")
        else:
            display_text_as_voice("I couldn't hear your age. Please say your age as a number.")
    
    elif st.session_state.booking_step == "gender":
        status_container.info("Listening for gender...")
        gender_input = listen_for_command()
        
        if gender_input:
            message_container.success(f"I heard: {gender_input}")
            gender_input = gender_input.lower()
            if "male" in gender_input and "female" not in gender_input:
                st.session_state.ticket_details['gender'] = "Male"
                display_text_as_voice("Gender recorded as Male. Now, please say your source station.")
            elif "female" in gender_input:
                st.session_state.ticket_details['gender'] = "Female"
                display_text_as_voice("Gender recorded as Female. Now, please say your source station.")
            else:
                st.session_state.ticket_details['gender'] = "Other"
                display_text_as_voice("Gender recorded as Other. Now, please say your source station.")
            
            # List some stations for reference
            stations = get_station_list()
            st.write("Available stations include:", ", ".join(stations[:10]) + "...")
            st.session_state.booking_step = "source"
        else:
            display_text_as_voice("I couldn't hear your gender. Please say Male, Female, or Other.")
    
    elif st.session_state.booking_step == "source":
        status_container.info("Listening for source station...")
        source_input = listen_for_command()
        
        if source_input:
            message_container.success(f"I heard: {source_input}")
            # Find best matching station
            stations = get_station_list()
            best_match = None
            best_score = 0
            
            for station in stations:
                if source_input.lower() in station.lower() or station.lower() in source_input.lower():
                    score = len(set(source_input.lower()) & set(station.lower()))
                    if score > best_score:
                        best_score = score
                        best_match = station
            
            if best_match:
                st.session_state.ticket_details['source'] = best_match
                display_text_as_voice(f"Source station recorded as {best_match}. Now, please say your destination station.")
                st.session_state.booking_step = "destination"
            else:
                station_examples = ", ".join(stations[:5])
                display_text_as_voice(f"I couldn't match your station. Please try again. Some examples are: {station_examples}")
        else:
            display_text_as_voice("I couldn't hear your source station. Please say the name of your departure station.")
    
    elif st.session_state.booking_step == "destination":
        status_container.info("Listening for destination station...")
        destination_input = listen_for_command()
        
        if destination_input:
            message_container.success(f"I heard: {destination_input}")
            # Find best matching station
            stations = get_station_list()
            best_match = None
            best_score = 0
            
            for station in stations:
                if destination_input.lower() in station.lower() or station.lower() in destination_input.lower():
                    score = len(set(destination_input.lower()) & set(station.lower()))
                    if score > best_score:
                        best_score = score
                        best_match = station
            
            if best_match:
                # Check if source and destination are the same
                if st.session_state.ticket_details.get('source') == best_match:
                    display_text_as_voice("Source and destination cannot be the same. Please choose a different destination.")
                else:
                    st.session_state.ticket_details['destination'] = best_match
                    
                    # Display ticket details for confirmation
                    details = st.session_state.ticket_details
                    display_text_as_voice(f"Destination recorded as {best_match}. Now, please say your travel date in the format month day, for example 'March 30' or say 'tomorrow'.")
                    st.session_state.booking_step = "travel_date"
            else:
                station_examples = ", ".join(stations[:5])
                display_text_as_voice(f"I couldn't match your station. Please try again. Some examples are: {station_examples}")
        else:
            display_text_as_voice("I couldn't hear your destination station. Please say the name of your arrival station.")
    
    elif st.session_state.booking_step == "travel_date":
        status_container.info("Listening for travel date...")
        date_input = listen_for_command()
        
        if date_input:
            message_container.success(f"I heard: {date_input}")
            date_input = date_input.lower()
            
            # Parse the date from the input
            travel_date = None
            
            if "tomorrow" in date_input:
                # Set date to tomorrow
                tomorrow = datetime.now() + timedelta(days=1)
                travel_date = tomorrow.strftime("%Y-%m-%d")
            elif "today" in date_input:
                # Set date to today
                travel_date = datetime.now().strftime("%Y-%m-%d") 
            else:
                # Try to extract a date (month and day)
                months = {
                    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
                    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
                }
                
                # Check for month names in the input
                month_num = None
                for month_name, month_value in months.items():
                    if month_name in date_input:
                        month_num = month_value
                        break
                
                # Extract day number
                day_match = re.search(r'\b(\d{1,2})\b', date_input)
                day_num = int(day_match.group(1)) if day_match else None
                
                if month_num and day_num:
                    # Get current year
                    current_year = datetime.now().year
                    
                    # Create date string
                    try:
                        travel_date = datetime(current_year, month_num, day_num).strftime("%Y-%m-%d")
                    except ValueError:
                        display_text_as_voice(f"Invalid date. Please provide a valid date.")
                        return
            
            if travel_date:
                st.session_state.ticket_details['travel_date'] = travel_date
                
                # Format date for speech
                # Convert YYYY-MM-DD to a more readable format
                date_obj = datetime.strptime(travel_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%B %d, %Y")
                
                display_text_as_voice(f"Travel date recorded as {formatted_date}.")
                
                # Display ticket details for confirmation
                details = st.session_state.ticket_details
                confirm_message = f"Please confirm: You want to book a ticket for {details['name']}, age {details['age']}, gender {details['gender']}, from {details['source']} to {details['destination']}, on {formatted_date}. Say 'Confirm' to book this ticket or 'Cancel' to abort."
                display_text_as_voice(confirm_message)
                st.session_state.booking_step = "confirm"
            else:
                display_text_as_voice("I couldn't understand the date. Please say a date like 'March 30' or 'tomorrow'.")
        else:
            display_text_as_voice("I couldn't hear your travel date. Please say a date like 'March 30' or 'tomorrow'.")
        
    elif st.session_state.booking_step == "confirm":
        status_container.info("Listening for confirmation...")
        confirm_input = listen_for_command()
        
        if confirm_input:
            message_container.success(f"I heard: {confirm_input}")
            
            if "confirm" in confirm_input.lower() or "yes" in confirm_input.lower():
                # Create the ticket
                ticket = book_ticket(
                    st.session_state.ticket_details['name'],
                    st.session_state.ticket_details['age'],
                    st.session_state.ticket_details['gender'],
                    st.session_state.ticket_details['source'],
                    st.session_state.ticket_details['destination'],
                    st.session_state.ticket_details.get('travel_date')
                )
                
                # Add to ticket list
                st.session_state.tickets.append(ticket)
                
                # Display immediate confirmation
                display_text_as_voice(f"Ticket booked successfully! Your ticket ID is {ticket['id']}. The ticket is now displayed on screen with a download option. Returning to main menu.")
                
                # Create a session state variable to store the current ticket for display and download
                st.session_state.current_ticket = ticket
                
                # Reset state but keep listening for next command
                st.session_state.show_success = True
                st.session_state.success_message = f"Ticket booked successfully! Your ticket ID is {ticket['id']}. What would you like to do next?"
                st.session_state.current_operation = None
                st.session_state.booking_step = None
                st.session_state.ticket_details = {}
                
                # Removed sleep to prevent blocking Streamlit execution
            
            elif "cancel" in confirm_input.lower() or "no" in confirm_input.lower():
                display_text_as_voice("Booking cancelled. Returning to main menu.")
                
                # Reset state
                st.session_state.current_operation = None
                st.session_state.booking_step = None
                st.session_state.ticket_details = {}
            
            else:
                display_text_as_voice("Please say 'Confirm' to book the ticket or 'Cancel' to abort.")
        else:
            display_text_as_voice("I couldn't hear your response. Please say 'Confirm' to book the ticket or 'Cancel' to abort.")

def process_modification():
    """Handle ticket modification process"""
    if 'modify_step' not in st.session_state:
        st.session_state.modify_step = "select_ticket"
    
    if st.session_state.modify_step == "select_ticket":
        status_container.info("Listening for ticket ID or passenger name...")
        ticket_input = listen_for_command()
        
        if ticket_input:
            message_container.success(f"I heard: {ticket_input}")
            
            # Try to extract ticket ID
            id_pattern = r'\b([A-Z0-9]{8})\b'
            id_match = re.search(id_pattern, ticket_input.upper())
            
            if id_match:
                # Processing by ticket ID
                ticket_id = id_match.group(1)
                ticket = get_ticket_by_id(ticket_id, st.session_state.tickets)
                
                if ticket:
                    st.session_state.selected_ticket_id = ticket_id
                    display_text_as_voice(f"Found ticket for {ticket['name']}. What would you like to modify? Say name, age, gender, source, or destination.")
                    st.session_state.modify_step = "select_field"
                else:
                    display_text_as_voice(f"No ticket found with ID {ticket_id}. Please try again.")
            else:
                # Try searching by name
                matching_tickets = get_tickets_by_name(ticket_input, st.session_state.tickets)
                
                if matching_tickets:
                    if len(matching_tickets) == 1:
                        # Single match found
                        ticket = matching_tickets[0]
                        st.session_state.selected_ticket_id = ticket['id']
                        display_text_as_voice(f"Found ticket for {ticket['name']}, from {ticket['source']} to {ticket['destination']}. What would you like to modify? Say name, age, gender, source, or destination.")
                        st.session_state.modify_step = "select_field"
                    else:
                        # Multiple matches found
                        display_text_as_voice(f"Found {len(matching_tickets)} tickets for '{ticket_input}'. Please choose one by saying the ticket ID:")
                        
                        for ticket in matching_tickets:
                            ticket_info = f"Ticket ID {ticket['id']}, {ticket['name']}, from {ticket['source']} to {ticket['destination']}"
                            display_text_as_voice(ticket_info)
                        
                        # Stay in select_ticket step but mark that we're selecting from multiple matches
                        st.session_state.selecting_from_matches = True
                else:
                    display_text_as_voice("No tickets found matching that name or ID. Please try again with a different name or ticket ID.")
        else:
            display_text_as_voice("I couldn't hear your command. Please say the ID or passenger name of the ticket you want to modify.")
    
    elif st.session_state.modify_step == "select_field":
        status_container.info("Listening for field to modify...")
        field_input = listen_for_command()
        
        if field_input:
            message_container.success(f"I heard: {field_input}")
            field = field_input.lower()
            
            ticket = get_ticket_by_id(st.session_state.selected_ticket_id, st.session_state.tickets)
            st.session_state.ticket_details = dict(ticket)  # Copy current details
            
            if "name" in field:
                display_text_as_voice(f"Current name is {ticket['name']}. Please say the new name.")
                st.session_state.modify_step = "update_name"
            
            elif "age" in field:
                display_text_as_voice(f"Current age is {ticket['age']}. Please say the new age.")
                st.session_state.modify_step = "update_age"
            
            elif "gender" in field:
                display_text_as_voice(f"Current gender is {ticket['gender']}. Please say the new gender.")
                st.session_state.modify_step = "update_gender"
            
            elif "source" in field:
                display_text_as_voice(f"Current source station is {ticket['source']}. Please say the new source station.")
                st.session_state.modify_step = "update_source"
            
            elif "destination" in field:
                display_text_as_voice(f"Current destination station is {ticket['destination']}. Please say the new destination station.")
                st.session_state.modify_step = "update_destination"
            
            elif "confirm" in field or "update" in field or "save" in field:
                # Save changes
                updated_ticket = modify_ticket(
                    st.session_state.selected_ticket_id,
                    st.session_state.ticket_details['name'],
                    st.session_state.ticket_details['age'],
                    st.session_state.ticket_details['gender'],
                    st.session_state.ticket_details['source'],
                    st.session_state.ticket_details['destination'],
                    st.session_state.tickets
                )
                
                if updated_ticket:
                    display_text_as_voice("Ticket updated successfully. Returning to main menu.")
                    
                    # Reset state with success message
                    st.session_state.show_success = True
                    st.session_state.success_message = "Ticket updated successfully! What would you like to do next?"
                    st.session_state.current_operation = None
                    st.session_state.modify_step = "select_ticket"
                    st.session_state.selected_ticket_id = None
                    st.session_state.ticket_details = {}
                    
                    # Force a rerun to immediately update the UI
                    # Removed sleep to prevent blocking Streamlit execution

                else:
                    display_text_as_voice("Error updating ticket. Please try again.")
                    
                    # Reset state
                    st.session_state.current_operation = None
                    st.session_state.modify_step = "select_ticket"
                    st.session_state.selected_ticket_id = None
                    st.session_state.ticket_details = {}
            
            elif "cancel" in field or "abort" in field:
                display_text_as_voice("Modification cancelled. Returning to main menu.")
                
                # Reset state
                st.session_state.current_operation = None
                st.session_state.modify_step = "select_ticket"
                st.session_state.selected_ticket_id = None
                st.session_state.ticket_details = {}
            
            else:
                display_text_as_voice("Please specify what you want to modify: name, age, gender, source, or destination. Or say 'Confirm' to save changes or 'Cancel' to abort.")
        else:
            display_text_as_voice("I couldn't hear your command. Please specify what you want to modify: name, age, gender, source, or destination.")
    
    elif st.session_state.modify_step == "update_name":
        status_container.info("Listening for new name...")
        name_input = listen_for_command()
        
        if name_input:
            message_container.success(f"I heard: {name_input}")
            st.session_state.ticket_details['name'] = name_input
            display_text_as_voice(f"Name updated to {name_input}. What else would you like to modify? Or say 'Confirm' to save changes.")
            st.session_state.modify_step = "select_field"
        else:
            display_text_as_voice("I couldn't hear your input. Please say the new name.")
    
    elif st.session_state.modify_step == "update_age":
        status_container.info("Listening for new age...")
        age_input = listen_for_command()
        
        if age_input:
            message_container.success(f"I heard: {age_input}")
            try:
                age_match = re.search(r'\b(\d+)\b', age_input)
                if age_match:
                    age = int(age_match.group(1))
                    if 1 <= age <= 120:
                        st.session_state.ticket_details['age'] = age
                        display_text_as_voice(f"Age updated to {age}. What else would you like to modify? Or say 'Confirm' to save changes.")
                        st.session_state.modify_step = "select_field"
                    else:
                        display_text_as_voice("Age must be between 1 and 120. Please try again.")
                else:
                    display_text_as_voice("I couldn't understand your age. Please say a number clearly.")
            except ValueError:
                display_text_as_voice("I couldn't understand your age. Please say a number clearly.")
        else:
            display_text_as_voice("I couldn't hear your input. Please say the new age.")
    
    elif st.session_state.modify_step == "update_gender":
        status_container.info("Listening for new gender...")
        gender_input = listen_for_command()
        
        if gender_input:
            message_container.success(f"I heard: {gender_input}")
            gender_input = gender_input.lower()
            if "male" in gender_input and "female" not in gender_input:
                st.session_state.ticket_details['gender'] = "Male"
                display_text_as_voice("Gender updated to Male. What else would you like to modify? Or say 'Confirm' to save changes.")
            elif "female" in gender_input:
                st.session_state.ticket_details['gender'] = "Female"
                display_text_as_voice("Gender updated to Female. What else would you like to modify? Or say 'Confirm' to save changes.")
            else:
                st.session_state.ticket_details['gender'] = "Other"
                display_text_as_voice("Gender updated to Other. What else would you like to modify? Or say 'Confirm' to save changes.")
            
            st.session_state.modify_step = "select_field"
        else:
            display_text_as_voice("I couldn't hear your input. Please say Male, Female, or Other.")
    
    elif st.session_state.modify_step == "update_source":
        status_container.info("Listening for new source station...")
        source_input = listen_for_command()
        
        if source_input:
            message_container.success(f"I heard: {source_input}")
            stations = get_station_list()
            best_match = None
            best_score = 0
            
            for station in stations:
                if source_input.lower() in station.lower() or station.lower() in source_input.lower():
                    score = len(set(source_input.lower()) & set(station.lower()))
                    if score > best_score:
                        best_score = score
                        best_match = station
            
            if best_match:
                st.session_state.ticket_details['source'] = best_match
                display_text_as_voice(f"Source station updated to {best_match}. What else would you like to modify? Or say 'Confirm' to save changes.")
                st.session_state.modify_step = "select_field"
            else:
                station_examples = ", ".join(stations[:5])
                display_text_as_voice(f"I couldn't match your station. Please try again. Some examples are: {station_examples}")
        else:
            display_text_as_voice("I couldn't hear your input. Please say the new source station.")
    
    elif st.session_state.modify_step == "update_destination":
        status_container.info("Listening for new destination station...")
        destination_input = listen_for_command()
        
        if destination_input:
            message_container.success(f"I heard: {destination_input}")
            stations = get_station_list()
            best_match = None
            best_score = 0
            
            for station in stations:
                if destination_input.lower() in station.lower() or station.lower() in destination_input.lower():
                    score = len(set(destination_input.lower()) & set(station.lower()))
                    if score > best_score:
                        best_score = score
                        best_match = station
            
            if best_match:
                if st.session_state.ticket_details['source'] == best_match:
                    display_text_as_voice("Source and destination cannot be the same. Please choose a different destination.")
                else:
                    st.session_state.ticket_details['destination'] = best_match
                    display_text_as_voice(f"Destination station updated to {best_match}. What else would you like to modify? Or say 'Confirm' to save changes.")
                    st.session_state.modify_step = "select_field"
            else:
                station_examples = ", ".join(stations[:5])
                display_text_as_voice(f"I couldn't match your station. Please try again. Some examples are: {station_examples}")
        else:
            display_text_as_voice("I couldn't hear your input. Please say the new destination station.")

def process_cancellation():
    """Handle ticket cancellation process"""
    if 'cancel_step' not in st.session_state:
        st.session_state.cancel_step = "select_ticket"
    
    if st.session_state.cancel_step == "select_ticket":
        status_container.info("Listening for ticket ID or passenger name...")
        ticket_input = listen_for_command()
        
        if ticket_input:
            message_container.success(f"I heard: {ticket_input}")
            
            # Try to extract ticket ID
            id_pattern = r'\b([A-Z0-9]{8})\b'
            id_match = re.search(id_pattern, ticket_input.upper())
            
            if id_match:
                # Processing by ticket ID
                ticket_id = id_match.group(1)
                ticket = get_ticket_by_id(ticket_id, st.session_state.tickets)
                
                if ticket:
                    st.session_state.selected_ticket_id = ticket_id
                    display_text_as_voice(f"Found ticket for {ticket['name']} from {ticket['source']} to {ticket['destination']}. Say 'Confirm' to cancel this ticket or 'No' to keep it.")
                    st.session_state.cancel_step = "confirm"
                else:
                    display_text_as_voice(f"No ticket found with ID {ticket_id}. Please try again.")
            else:
                # Try searching by name
                matching_tickets = get_tickets_by_name(ticket_input, st.session_state.tickets)
                
                if matching_tickets:
                    if len(matching_tickets) == 1:
                        # Single match found
                        ticket = matching_tickets[0]
                        st.session_state.selected_ticket_id = ticket['id']
                        display_text_as_voice(f"Found ticket for {ticket['name']}, from {ticket['source']} to {ticket['destination']}. Say 'Confirm' to cancel this ticket or 'No' to keep it.")
                        st.session_state.cancel_step = "confirm"
                    else:
                        # Multiple matches found
                        display_text_as_voice(f"Found {len(matching_tickets)} tickets for '{ticket_input}'. Please choose one by saying the ticket ID:")
                        
                        for ticket in matching_tickets:
                            ticket_info = f"Ticket ID {ticket['id']}, {ticket['name']}, from {ticket['source']} to {ticket['destination']}"
                            display_text_as_voice(ticket_info)
                        
                        # Stay in select_ticket step for user to provide an ID
                else:
                    display_text_as_voice("No tickets found matching that name or ID. Please try again with a different name or ticket ID.")
        else:
            display_text_as_voice("I couldn't hear your command. Please say the ID or passenger name of the ticket you want to cancel.")
    
    elif st.session_state.cancel_step == "confirm":
        status_container.info("Listening for confirmation...")
        confirm_input = listen_for_command()
        
        if confirm_input:
            message_container.success(f"I heard: {confirm_input}")
            
            if "confirm" in confirm_input.lower() or "yes" in confirm_input.lower() or "delete" in confirm_input.lower():
                # Cancel the ticket
                success = cancel_ticket(st.session_state.selected_ticket_id, st.session_state.tickets)
                
                if success:
                    display_text_as_voice("Ticket cancelled successfully. Returning to main menu.")
                    
                    # Reset state with success message
                    st.session_state.show_success = True
                    st.session_state.success_message = "Ticket cancelled successfully! What would you like to do next?"
                    st.session_state.current_operation = None
                    st.session_state.cancel_step = "select_ticket"
                    st.session_state.selected_ticket_id = None
                    
                    # Force a rerun to immediately update the UI
                    # Removed sleep to prevent blocking Streamlit execution

                else:
                    display_text_as_voice("Error cancelling ticket. Please try again.")
                    
                    # Reset state
                    st.session_state.current_operation = None
                    st.session_state.cancel_step = "select_ticket"
                    st.session_state.selected_ticket_id = None
            
            elif "no" in confirm_input.lower() or "keep" in confirm_input.lower() or "don't" in confirm_input.lower():
                display_text_as_voice("Cancellation aborted. Ticket is kept. Returning to main menu.")
                
                # Reset state
                st.session_state.current_operation = None
                st.session_state.cancel_step = "select_ticket"
                st.session_state.selected_ticket_id = None
            
            else:
                display_text_as_voice("Please say 'Confirm' to cancel the ticket or 'No' to keep it.")
        else:
            display_text_as_voice("I couldn't hear your command. Please say 'Confirm' to cancel the ticket or 'No' to keep it.")

# Main application
def process_view():
    """Handle view tickets process"""
    if 'view_step' not in st.session_state:
        st.session_state.view_step = "display_options"
    
    # Display instruction and add ticket browser section
    st.write("## View Your Tickets")
    
    # Create a dedicated area for ticket display and download
    ticket_display = st.container()
    ticket_download_area = st.container()
    
    if st.session_state.view_step == "display_options":
        status_container.info("Listening for viewing option...")
        view_input = listen_for_command()
        
        if view_input:
            message_container.success(f"I heard: {view_input}")
            view_input = view_input.lower()
            
            # Check for "view a ticket" or "view ticket" type commands
            if ("view" in view_input and "ticket" in view_input) or "ticket id" in view_input:
                # Look for a ticket ID pattern anywhere in the input
                id_pattern = r'\b([A-Z0-9]{8})\b'
                id_match = re.search(id_pattern, view_input.upper())
                
                if id_match:
                    # Found a ticket ID
                    ticket_id = id_match.group(1)
                    st.write(f"Looking up ticket ID: {ticket_id}")
                else:
                    # No ticket ID found, ask for one
                    display_text_as_voice("Please say the ticket ID you want to view.")
                    st.session_state.view_step = "ask_id"
                    return
            # Check if it's a direct "download" command with ticket ID
            elif "download" in view_input:
                # Look for ticket ID in download command
                id_pattern = r'\b([A-Z0-9]{8})\b'
                id_match = re.search(id_pattern, view_input.upper())
                
                if id_match:
                    # Found a specific ticket ID to download
                    ticket_id = id_match.group(1)
                elif hasattr(st.session_state, 'last_viewed_ticket_id'):
                    # Use the last viewed ticket ID if available
                    ticket_id = st.session_state.last_viewed_ticket_id
                    display_text_as_voice(f"Preparing to download your last viewed ticket.")
                else:
                    # No ticket ID found and no recently viewed ticket
                    display_text_as_voice("I don't know which ticket to download. Please view a ticket first.")
                    return
                
                # Set up for download and trigger it immediately
                st.session_state.view_step = "download_ticket"
                st.session_state.ticket_id_to_download = ticket_id
                st.rerun()
                return
            # Check if it's just a standalone ticket ID
            else:
                # Look for a ticket ID pattern
                id_pattern = r'\b([A-Z0-9]{8})\b'
                id_match = re.search(id_pattern, view_input.upper())
                
                if id_match:
                    # Found a direct ticket ID input
                    ticket_id = id_match.group(1)
                    st.write(f"Looking up ticket ID: {ticket_id}")
                # Check for "all tickets" or similar commands
                elif "all" in view_input or "show all" in view_input or "list all" in view_input:
                    # Show all tickets section below
                    ticket_id = None
                else:
                    # Try to search by name
                    ticket_id = None
            
            # Continue with ticket ID lookup if we found one
            if ticket_id:
                ticket = get_ticket_by_id(ticket_id, st.session_state.tickets)
                
                if ticket:
                    # Format travel date for speech if it exists
                    travel_date_str = ""
                    if "travel_date" in ticket:
                        try:
                            date_obj = datetime.strptime(ticket["travel_date"], "%Y-%m-%d")
                            formatted_date = date_obj.strftime("%B %d, %Y")
                            travel_date_str = f", traveling on {formatted_date}"
                        except:
                            pass
                    
                    # Display ticket in dedicated container
                    with ticket_display:
                        st.subheader(f"Ticket Details: ID {ticket['id']}")
                        st.write(f"**Passenger:** {ticket['name']}")
                        st.write(f"**Age:** {ticket['age']}")
                        st.write(f"**Gender:** {ticket['gender']}")
                        st.write(f"**From:** {ticket['source']}")
                        st.write(f"**To:** {ticket['destination']}")
                        if "travel_date" in ticket:
                            st.write(f"**Travel Date:** {travel_date_str.replace(', traveling on ', '')}")
                        st.write(f"**Booking Time:** {ticket['booking_time']}")
                    
                    ticket_info = f"Found ticket ID {ticket['id']} for {ticket['name']}, age {ticket['age']}, gender {ticket['gender']}, " + \
                                f"from {ticket['source']} to {ticket['destination']}{travel_date_str}, booked on {ticket['booking_time']}"
                    display_text_as_voice(ticket_info)
                    
                    # Show ticket download option in dedicated area - improved for better visibility
                    with ticket_download_area:
                        st.subheader("📥 Download Your Ticket")
                        download_link = get_ticket_download_link(ticket)
                        st.markdown(download_link, unsafe_allow_html=True)
                        st.info("To download the ticket, click on the blue download button above or say 'download ticket'.")
                    
                    display_text_as_voice("You can download your ticket as a PDF file using the download link on the screen. Say 'download ticket' to get your ticket.")
                    
                    # Store current ticket ID for potential download command
                    st.session_state.last_viewed_ticket_id = ticket['id']
                    
                    # Set up for download option
                    st.session_state.ticket_id_to_download = ticket['id']
                    
                    # Reset state but keep view context
                    st.session_state.current_operation = "view"
                    st.session_state.view_step = "view_options"
                else:
                    display_text_as_voice(f"No ticket found with ID {ticket_id}. Please try again.")
            
            elif "all" in view_input or "show all" in view_input or "list all" in view_input:
                # Show all tickets
                if st.session_state.tickets:
                    display_text_as_voice(f"You have {len(st.session_state.tickets)} tickets. Here are your tickets:")
                    for idx, ticket in enumerate(st.session_state.tickets):
                        # Format travel date for speech if it exists
                        travel_date_str = ""
                        if "travel_date" in ticket:
                            try:
                                date_obj = datetime.strptime(ticket["travel_date"], "%Y-%m-%d")
                                formatted_date = date_obj.strftime("%B %d, %Y")
                                travel_date_str = f", traveling on {formatted_date}"
                            except:
                                pass
                                
                        ticket_info = f"Ticket {idx+1}, ID {ticket['id']}, {ticket['name']}, age {ticket['age']}, " + \
                                    f"from {ticket['source']} to {ticket['destination']}{travel_date_str}, booked on {ticket['booking_time']}"
                        display_text_as_voice(ticket_info)
                    display_text_as_voice("End of ticket list. Say a new command to continue.")
                    
                    # Reset state
                    st.session_state.current_operation = None
                    st.session_state.view_step = None
                else:
                    display_text_as_voice("You don't have any tickets. Say 'Book a ticket' to create a new booking.")
                    
                    # Reset state
                    st.session_state.current_operation = None
                    st.session_state.view_step = None
            else:
                # Search for tickets by name
                matching_tickets = get_tickets_by_name(view_input, st.session_state.tickets)
                
                if matching_tickets:
                    display_text_as_voice(f"Found {len(matching_tickets)} tickets for name containing '{view_input}':")
                    for idx, ticket in enumerate(matching_tickets):
                        # Format travel date for speech if it exists
                        travel_date_str = ""
                        if "travel_date" in ticket:
                            try:
                                date_obj = datetime.strptime(ticket["travel_date"], "%Y-%m-%d")
                                formatted_date = date_obj.strftime("%B %d, %Y")
                                travel_date_str = f", traveling on {formatted_date}"
                            except:
                                pass
                                
                        ticket_info = f"Ticket {idx+1}, ID {ticket['id']}, {ticket['name']}, age {ticket['age']}, " + \
                                    f"from {ticket['source']} to {ticket['destination']}{travel_date_str}, booked on {ticket['booking_time']}"
                        display_text_as_voice(ticket_info)
                    display_text_as_voice("End of ticket list. Say a new command to continue.")
                    
                    # Reset state
                    st.session_state.current_operation = None
                    st.session_state.view_step = None
                else:
                    display_text_as_voice(f"No tickets found for name containing '{view_input}'. Say 'Book a ticket' to create a new booking.")
                    
                    # Reset state
                    st.session_state.current_operation = None
                    st.session_state.view_step = None
        else:
            display_text_as_voice("I couldn't hear your input. Please say a ticket ID, name, or 'All tickets' to see all bookings.")
    
    elif st.session_state.view_step == "ask_name":
        status_container.info("Listening for name...")
        name_input = listen_for_command()
        
        if name_input:
            message_container.success(f"I heard: {name_input}")
            # Search for tickets by name
            matching_tickets = get_tickets_by_name(name_input, st.session_state.tickets)
            
            if matching_tickets:
                display_text_as_voice(f"Found {len(matching_tickets)} tickets for name containing '{name_input}':")
                for idx, ticket in enumerate(matching_tickets):
                    # Format travel date for speech if it exists
                    travel_date_str = ""
                    if "travel_date" in ticket:
                        try:
                            date_obj = datetime.strptime(ticket["travel_date"], "%Y-%m-%d")
                            formatted_date = date_obj.strftime("%B %d, %Y")
                            travel_date_str = f", traveling on {formatted_date}"
                        except:
                            pass
                            
                    ticket_info = f"Ticket {idx+1}, ID {ticket['id']}, {ticket['name']}, age {ticket['age']}, " + \
                                f"from {ticket['source']} to {ticket['destination']}{travel_date_str}, booked on {ticket['booking_time']}"
                    display_text_as_voice(ticket_info)
                display_text_as_voice("End of ticket list. Say a new command to continue.")
                
                # Reset state
                st.session_state.current_operation = None
                st.session_state.view_step = None
            else:
                display_text_as_voice(f"No tickets found for name containing '{name_input}'. Say 'Book a ticket' to create a new booking.")
                
                # Reset state
                st.session_state.current_operation = None
                st.session_state.view_step = None
        else:
            display_text_as_voice("I couldn't hear your input. Please say a name to search for.")
            
    elif st.session_state.view_step == "ask_id":
        status_container.info("Listening for ticket ID...")
        id_input = listen_for_command()
        
        if id_input:
            message_container.success(f"I heard: {id_input}")
            
            # Try to extract ticket ID
            id_pattern = r'\b([A-Z0-9]{8})\b'
            id_match = re.search(id_pattern, id_input.upper())
            
            if id_match:
                ticket_id = id_match.group(1)
                ticket = get_ticket_by_id(ticket_id, st.session_state.tickets)
                
                if ticket:
                    # Format travel date for speech if it exists
                    travel_date_str = ""
                    if "travel_date" in ticket:
                        try:
                            date_obj = datetime.strptime(ticket["travel_date"], "%Y-%m-%d")
                            formatted_date = date_obj.strftime("%B %d, %Y")
                            travel_date_str = f", traveling on {formatted_date}"
                        except:
                            pass
                    
                    ticket_info = f"Found ticket ID {ticket['id']} for {ticket['name']}, age {ticket['age']}, gender {ticket['gender']}, " + \
                                f"from {ticket['source']} to {ticket['destination']}{travel_date_str}, booked on {ticket['booking_time']}"
                    display_text_as_voice(ticket_info)
                    
                    # Show ticket download option
                    download_link = get_ticket_download_link(ticket)
                    st.markdown(download_link, unsafe_allow_html=True)
                    display_text_as_voice("You can download your ticket as a PDF file using the download link on the screen.")
                    
                    # Reset state
                    st.session_state.current_operation = None
                    st.session_state.view_step = None
                else:
                    display_text_as_voice(f"No ticket found with ID {ticket_id}. Please try again or say 'main menu' to return.")
            else:
                display_text_as_voice("I couldn't recognize a ticket ID in what you said. Ticket IDs consist of 8 letters and numbers. Please try again or say 'main menu' to return.")
        else:
            display_text_as_voice("I couldn't hear your input. Please say the ticket ID clearly.")
            
    elif st.session_state.view_step == "download_ticket" or st.session_state.view_step == "view_options":
        # Handle direct download request or other view options
        if st.session_state.view_step == "download_ticket" and hasattr(st.session_state, 'ticket_id_to_download'):
            ticket_id = st.session_state.ticket_id_to_download
            ticket = get_ticket_by_id(ticket_id, st.session_state.tickets)
            
            if ticket:
                # Create a dedicated area for ticket display and download
                download_container = st.container()
                
                # Create a prominent download section with clear visual guidance
                with download_container:
                    st.subheader(f"📄 Download Ticket ID: {ticket_id}")
                    st.success(f"Ready to download ticket for {ticket['name']}")
                    
                    # Format travel date for display if it exists
                    travel_date_display = ""
                    if "travel_date" in ticket:
                        try:
                            date_obj = datetime.strptime(ticket["travel_date"], "%Y-%m-%d")
                            travel_date_display = date_obj.strftime("%B %d, %Y")
                        except:
                            pass
                    
                    # Display ticket summary
                    st.write(f"**Passenger:** {ticket['name']}")
                    st.write(f"**Journey:** {ticket['source']} to {ticket['destination']}")
                    if travel_date_display:
                        st.write(f"**Travel Date:** {travel_date_display}")
                    
                    # Create prominent download button with improved styling
                    download_link = get_ticket_download_link(ticket)
                    st.markdown(download_link, unsafe_allow_html=True)
                    st.info("The blue button above ☝️ will download your ticket as a PDF file. Click it to save your ticket.")
                
                # Voice guidance with clear instructions
                display_text_as_voice(f"Your ticket for {ticket['name']} traveling from {ticket['source']} to {ticket['destination']} is ready for download. Click the Download Ticket PDF button on your screen. It's a large blue button near the middle of the screen.")
                
                # Reset state after providing the download, but give users time to download
                st.session_state.current_operation = None
                st.session_state.view_step = None
                if hasattr(st.session_state, 'ticket_id_to_download'):
                    delattr(st.session_state, 'ticket_id_to_download')
            else:
                display_text_as_voice(f"Sorry, I couldn't find a ticket with ID {ticket_id}. Please try again with a valid ticket ID.")
                st.session_state.view_step = "display_options"
        
        elif st.session_state.view_step == "view_options":
            # Listen for next command related to viewing
            status_container.info("Listening for next viewing option...")
            next_command = listen_for_command()
            
            if next_command:
                message_container.success(f"I heard: {next_command}")
                next_command = next_command.lower()
                
                # First check if we need to download a ticket
                if "download" in next_command:
                    # Check if there's a specific ticket ID in the download command
                    id_pattern = r'\b([A-Z0-9]{8})\b'
                    id_match = re.search(id_pattern, next_command.upper())
                    
                    if id_match:
                        # User specified a ticket ID to download
                        ticket_id = id_match.group(1)
                        st.session_state.ticket_id_to_download = ticket_id
                    elif hasattr(st.session_state, 'last_viewed_ticket_id'):
                        # Use the last viewed ticket ID
                        ticket_id = st.session_state.last_viewed_ticket_id
                        st.session_state.ticket_id_to_download = ticket_id
                    else:
                        # No ticket ID found and no last viewed ticket
                        display_text_as_voice("I don't have a ticket ID to download. Please view a ticket first by saying a ticket ID.")
                        st.session_state.view_step = "display_options"
                        return
                    
                    # Now check if the ticket exists
                    ticket = get_ticket_by_id(st.session_state.ticket_id_to_download, st.session_state.tickets)
                    if ticket:
                        # Ticket exists, proceed with download
                        st.session_state.view_step = "download_ticket"
                        # Use rerun to refresh and show download immediately
                        st.success(f"Preparing to download ticket {ticket_id}...")
                        st.rerun()
                    else:
                        # Ticket not found with this ID
                        display_text_as_voice(f"Sorry, I couldn't find ticket with ID {ticket_id}. Please try again.")
                        st.session_state.view_step = "display_options"
                        if hasattr(st.session_state, 'ticket_id_to_download'):
                            delattr(st.session_state, 'ticket_id_to_download')
                elif "main" in next_command or "menu" in next_command or "back" in next_command:
                    # Return to main menu
                    st.session_state.current_operation = None
                    st.session_state.view_step = None
                    display_text_as_voice("Returning to main menu. Say a new command.")
                else:
                    # Handle any other view commands
                    st.session_state.view_step = "display_options"
                    return
            else:
                display_text_as_voice("I couldn't hear your command. Say 'download ticket' to download or 'main menu' to return.")

def main():
    """Main application execution"""
    # Show success message when returning to main menu
    if 'show_success' in st.session_state and st.session_state.show_success:
        display_text_as_voice(st.session_state.success_message)
        st.session_state.show_success = False
        st.session_state.success_message = ""
        # Removed sleep to prevent blocking
        
    # Display and provide download for current ticket if available
    if 'current_ticket' in st.session_state and st.session_state.current_ticket:
        ticket = st.session_state.current_ticket
        
        # Display ticket details in a nice format
        st.markdown("## 🎫 Your Ticket Details")
        st.markdown(f"**Ticket ID:** {ticket['id']}")
        st.markdown(f"**Passenger:** {ticket['name']}")
        st.markdown(f"**Age:** {ticket['age']}")
        st.markdown(f"**Gender:** {ticket['gender']}")
        st.markdown(f"**From:** {ticket['source']}")
        st.markdown(f"**To:** {ticket['destination']}")
        
        # Display travel date if available
        if 'travel_date' in ticket and ticket['travel_date']:
            try:
                date_obj = datetime.strptime(ticket['travel_date'], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%B %d, %Y")
                st.markdown(f"**Travel Date:** {formatted_date}")
            except:
                st.markdown(f"**Travel Date:** {ticket['travel_date']}")
        
        st.markdown(f"**Booking Time:** {ticket['booking_time']}")
        
        # Display download link for the ticket
        ticket_download_html = get_ticket_download_link(ticket)
        st.markdown(ticket_download_html, unsafe_allow_html=True)
        
        # Clear the current ticket after displaying
        st.session_state.current_ticket = None
        
    # Process based on the current operation
    if st.session_state.current_operation is None:
        process_main_menu()
    elif st.session_state.current_operation == "book":
        process_booking()
    elif st.session_state.current_operation == "modify":
        process_modification()
    elif st.session_state.current_operation == "cancel":
        process_cancellation()
    elif st.session_state.current_operation == "view":
        process_view()

# Run the application
if __name__ == "__main__":
    main()
    # Auto rerun to keep listening - no sleep needed
    st.rerun()