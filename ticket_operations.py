import uuid
from datetime import datetime, timedelta

def book_ticket(name, age, gender, source, destination, travel_date=None):
    """
    Create a new ticket with the provided information
    
    Args:
        name (str): Passenger name
        age (int): Passenger age
        gender (str): Passenger gender
        source (str): Source station
        destination (str): Destination station
        travel_date (str, optional): Date of travel. Defaults to tomorrow.
        
    Returns:
        dict: Newly created ticket
    """
    # Generate a unique ticket ID
    ticket_id = str(uuid.uuid4())[:8].upper()
    
    # Set default travel date to tomorrow if not provided
    if not travel_date:
        tomorrow = datetime.now() + timedelta(days=1)
        travel_date = tomorrow.strftime("%Y-%m-%d")
    
    # Create ticket object
    ticket = {
        "id": ticket_id,
        "name": name,
        "age": age,
        "gender": gender,
        "source": source,
        "destination": destination,
        "travel_date": travel_date,
        "booking_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return ticket

def modify_ticket(ticket_id, name, age, gender, source, destination, tickets, travel_date=None):
    """
    Modify an existing ticket
    
    Args:
        ticket_id (str): ID of the ticket to modify
        name (str): Updated passenger name
        age (int): Updated passenger age
        gender (str): Updated passenger gender
        source (str): Updated source station
        destination (str): Updated destination station
        tickets (list): List of all tickets
        travel_date (str, optional): Updated date of travel. Defaults to None.
        
    Returns:
        dict: Updated ticket or None if not found
    """
    for i, ticket in enumerate(tickets):
        if ticket["id"] == ticket_id:
            # Keep existing travel date if not provided
            if not travel_date and "travel_date" in ticket:
                travel_date = ticket["travel_date"]
            # Set default travel date to tomorrow if there was no existing date
            elif not travel_date:
                tomorrow = datetime.now() + timedelta(days=1)
                travel_date = tomorrow.strftime("%Y-%m-%d")
            
            # Update ticket with new information
            updated_ticket = {
                "id": ticket_id,
                "name": name,
                "age": age,
                "gender": gender,
                "source": source,
                "destination": destination,
                "travel_date": travel_date,
                "booking_time": ticket["booking_time"]  # Keep original booking time
            }
            
            # Replace the old ticket with the updated one
            tickets[i] = updated_ticket
            return updated_ticket
    
    return None

def cancel_ticket(ticket_id, tickets):
    """
    Cancel (remove) a ticket
    
    Args:
        ticket_id (str): ID of the ticket to cancel
        tickets (list): List of all tickets
        
    Returns:
        bool: True if ticket was canceled, False otherwise
    """
    for i, ticket in enumerate(tickets):
        if ticket["id"] == ticket_id:
            # Remove the ticket from the list
            tickets.pop(i)
            return True
    
    return False

def get_all_tickets(tickets):
    """
    Get all tickets
    
    Args:
        tickets (list): List of all tickets
        
    Returns:
        list: All tickets
    """
    return tickets

def get_ticket_by_id(ticket_id, tickets):
    """
    Get a specific ticket by ID
    
    Args:
        ticket_id (str): Ticket ID to find
        tickets (list): List of all tickets
        
    Returns:
        dict: Ticket object or None if not found
    """
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    
    return None

def get_tickets_by_name(name, tickets):
    """
    Get all tickets for a passenger by name
    
    Args:
        name (str): Passenger name to search for
        tickets (list): List of all tickets
        
    Returns:
        list: List of matching tickets
    """
    matching_tickets = []
    name = name.lower()
    
    for ticket in tickets:
        # Check for partial match in names
        if name in ticket["name"].lower():
            matching_tickets.append(ticket)
    
    return matching_tickets
