def get_station_list():
    """
    Returns a list of railway stations
    
    Returns:
        list: List of railway station names
    """
    # List of common railway stations
    stations = [
        "New Delhi",
        "Mumbai Central",
        "Chennai Central",
        "Howrah",
        "Bengaluru",
        "Hyderabad",
        "Ahmedabad",
        "Jaipur",
        "Pune",
        "Lucknow",
        "Kanpur",
        "Patna",
        "Bhopal",
        "Chandigarh",
        "Guwahati",
        "Thiruvananthapuram",
        "Kochi",
        "Visakhapatnam",
        "Bhubaneswar",
        "Nagpur",
        "Amritsar",
        "Jammu",
        "Dehradun",
        "Raipur",
        "Ranchi",
        "Gwalior",
        "Varanasi",
        "Agra",
        "Allahabad",
        "Surat"
    ]
    
    # Sort stations alphabetically for easier selection
    return sorted(stations)
