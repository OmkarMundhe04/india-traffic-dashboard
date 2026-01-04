"""
Utility functions for traffic dashboard
"""


def normalize_congestion(congestion):
    """
    Normalize congestion percentage to 0-1 scale for heatmap
    
    Args:
        congestion: Congestion percentage (0-100)
        
    Returns:
        float: Normalized value (0-1)
    """
    return min(max(congestion / 100, 0), 1.0)


def congestion_to_color(congestion):
    """
    Return color code based on congestion level
    
    Args:
        congestion: Congestion percentage (0-100)
        
    Returns:
        str: Hex color code
    """
    if congestion < 30:
        return "#48bb78"  # Green - Free flow
    elif congestion < 60:
        return "#ecc94b"  # Yellow - Moderate
    else:
        return "#f56565"  # Red - Heavy congestion


def radius_from_congestion(congestion):
    """
    Calculate marker radius based on congestion level
    Higher congestion = larger marker
    
    Args:
        congestion: Congestion percentage (0-100)
        
    Returns:
        int: Marker radius in pixels
    """
    # Range: 5px (low congestion) to 20px (high congestion)
    return int(5 + (congestion / 100) * 15)


def get_congestion_status(congestion):
    """
    Get human-readable status from congestion percentage
    
    Args:
        congestion: Congestion percentage (0-100)
        
    Returns:
        tuple: (status_text, emoji, color)
    """
    if congestion < 30:
        return "Free Flow", "🟢", "#48bb78"
    elif congestion < 60:
        return "Moderate Traffic", "🟡", "#ecc94b"
    else:
        return "Heavy Congestion", "🔴", "#f56565"


def get_traffic_advice(congestion):
    """
    Get traffic advice based on congestion level
    
    Args:
        congestion: Congestion percentage (0-100)
        
    Returns:
        str: Traffic advice message
    """
    if congestion < 30:
        return "Traffic is moving smoothly. Excellent time to travel!"
    elif congestion < 45:
        return "Light traffic. Good conditions for travel with minimal delays."
    elif congestion < 60:
        return "Moderate traffic. Expect some delays. Plan extra time."
    elif congestion < 75:
        return "Heavy traffic. Significant delays expected. Consider alternate routes."
    else:
        return "Severe congestion. Major delays. Avoid if possible or use public transport."


def format_speed(speed):
    """
    Format speed value for display
    
    Args:
        speed: Speed in km/h (can be number or "N/A")
        
    Returns:
        str: Formatted speed string
    """
    if isinstance(speed, (int, float)):
        return f"{speed:.1f} km/h"
    return str(speed)


def calculate_eta_multiplier(congestion):
    """
    Calculate ETA multiplier based on congestion
    Used to estimate how much longer a journey will take
    
    Args:
        congestion: Congestion percentage (0-100)
        
    Returns:
        float: Multiplier (1.0 = normal time, 2.0 = double time)
    """
    # Linear interpolation: 0% = 1x, 100% = 3x
    return 1.0 + (congestion / 100) * 2.0


def get_rush_hour_info(hour):
    """
    Get rush hour information for a given hour
    
    Args:
        hour: Hour of day (0-23)
        
    Returns:
        dict: Rush hour info with status and description
    """
    if 7 <= hour <= 10:
        return {
            "is_rush_hour": True,
            "period": "Morning Rush",
            "description": "High traffic - Morning commute hours",
            "icon": "🌅"
        }
    elif 17 <= hour <= 20:
        return {
            "is_rush_hour": True,
            "period": "Evening Rush",
            "description": "High traffic - Evening commute hours",
            "icon": "🌆"
        }
    elif 0 <= hour <= 6:
        return {
            "is_rush_hour": False,
            "period": "Night",
            "description": "Low traffic - Late night/early morning",
            "icon": "🌙"
        }
    else:
        return {
            "is_rush_hour": False,
            "period": "Off-Peak",
            "description": "Moderate traffic - Off-peak hours",
            "icon": "☀️"
        }


def categorize_congestion(congestion):
    """
    Categorize congestion into levels
    
    Args:
        congestion: Congestion percentage (0-100)
        
    Returns:
        str: Category name
    """
    if congestion < 30:
        return "Low"
    elif congestion < 60:
        return "Moderate"
    elif congestion < 80:
        return "High"
    else:
        return "Severe"