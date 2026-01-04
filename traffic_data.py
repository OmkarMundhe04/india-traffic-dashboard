import requests
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_traffic_from_tomtom(lat, lon, api_key):
    """
    Fetch real traffic data from TomTom Traffic Flow API
    
    Args:
        lat: Latitude
        lon: Longitude
        api_key: TomTom API key
        
    Returns:
        tuple: (congestion_percentage, source, current_speed, free_flow_speed)
    """
    try:
        url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
        
        params = {
            "key": api_key,
            "point": f"{lat},{lon}",
            "unit": "KMPH"
        }
        
        logger.info(f"🌐 Requesting TomTom data for ({lat}, {lon})")
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            flow_data = data.get("flowSegmentData", {})
            current_speed = flow_data.get("currentSpeed", 0)
            free_flow_speed = flow_data.get("freeFlowSpeed", 1)
            current_travel_time = flow_data.get("currentTravelTime", 0)
            free_flow_travel_time = flow_data.get("freeFlowTravelTime", 1)
            confidence = flow_data.get("confidence", 0)
            
            # Calculate congestion based on speed ratio
            if free_flow_speed > 0:
                speed_ratio = current_speed / free_flow_speed
                congestion = round((1 - speed_ratio) * 100, 1)
                
                # Clamp between 0 and 100
                congestion = max(0, min(100, congestion))
                
                logger.info(
                    f"✅ TomTom Success: {congestion}% congestion "
                    f"(Speed: {current_speed}/{free_flow_speed} km/h, "
                    f"Confidence: {confidence:.0%})"
                )
                
                return congestion, "TomTom Traffic API", current_speed, free_flow_speed
            else:
                logger.warning("⚠️ TomTom: Invalid speed data")
                return None, "TomTom Failed", "N/A", "N/A"
                
        elif response.status_code == 401:
            logger.error("❌ TomTom: Authentication failed - Invalid API key")
            return None, "TomTom Auth Failed", "N/A", "N/A"
        elif response.status_code == 403:
            logger.error("❌ TomTom: Access forbidden - Check API permissions")
            return None, "TomTom Forbidden", "N/A", "N/A"
        elif response.status_code == 429:
            logger.error("❌ TomTom: Rate limit exceeded")
            return None, "TomTom Rate Limited", "N/A", "N/A"
        else:
            logger.warning(f"⚠️ TomTom: Unexpected status {response.status_code}")
            logger.debug(f"Response: {response.text[:200]}")
            return None, "TomTom Failed", "N/A", "N/A"
            
    except requests.exceptions.Timeout:
        logger.error("⏱️ TomTom: Request timeout")
        return None, "TomTom Timeout", "N/A", "N/A"
    except requests.exceptions.ConnectionError:
        logger.error("❌ TomTom: Connection error")
        return None, "TomTom Connection Failed", "N/A", "N/A"
    except Exception as e:
        logger.error(f"❌ TomTom: Unexpected error - {str(e)}")
        return None, "TomTom Error", "N/A", "N/A"


def get_traffic_from_mapmyindia(lat, lon, api_key):
    """
    Fetch traffic data from MapmyIndia Route API
    
    Args:
        lat: Latitude
        lon: Longitude  
        api_key: MapmyIndia API key
        
    Returns:
        tuple: (congestion_percentage, source, current_speed, free_flow_speed)
    """
    try:
        # Create a short route to measure traffic
        start_lon, start_lat = lon, lat
        end_lon, end_lat = lon + 0.01, lat + 0.01  # ~1km route
        
        url = f"https://apis.mapmyindia.com/advancedmaps/v1/{api_key}/route_adv/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
        
        params = {
            "rtype": 1,  # Get traffic info
            "region": "ind"
        }
        
        logger.info(f"🌐 Requesting MapmyIndia data for ({lat}, {lon})")
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if "routes" in data and len(data["routes"]) > 0:
                route = data["routes"][0]
                duration = route.get("duration", 0)  # seconds
                distance = route.get("distance", 1)  # meters
                
                # Calculate average speed
                if distance > 0 and duration > 0:
                    current_speed = (distance / 1000) / (duration / 3600)  # km/h
                    
                    # Estimate free flow speed (assume 50 km/h in city)
                    free_flow_speed = 50
                    
                    # Calculate congestion
                    speed_ratio = current_speed / free_flow_speed
                    congestion = round((1 - speed_ratio) * 100, 1)
                    congestion = max(0, min(100, congestion))
                    
                    logger.info(
                        f"✅ MapmyIndia Success: {congestion}% congestion "
                        f"(Speed: {current_speed:.1f} km/h)"
                    )
                    
                    return congestion, "MapmyIndia Route API", round(current_speed, 1), free_flow_speed
                    
        elif response.status_code == 401:
            logger.error("❌ MapmyIndia: Authentication failed")
            return None, "MapmyIndia Auth Failed", "N/A", "N/A"
        else:
            logger.warning(f"⚠️ MapmyIndia: Status {response.status_code}")
            return None, "MapmyIndia Failed", "N/A", "N/A"
            
    except Exception as e:
        logger.error(f"❌ MapmyIndia: Error - {str(e)}")
        return None, "MapmyIndia Error", "N/A", "N/A"


def get_simulated_congestion(city, lat, lon):
    """
    Intelligent traffic simulation based on time, location, and patterns
    
    Args:
        city: City name
        lat: Latitude
        lon: Longitude
        
    Returns:
        tuple: (congestion_percentage, source, current_speed, free_flow_speed)
    """
    # Create deterministic seed from city name and coordinates
    seed = sum(ord(c) for c in city) + int(lat * 100) + int(lon * 100)
    
    # Get current time factors
    now = datetime.now()
    hour = now.hour
    day_of_week = now.weekday()  # 0 = Monday, 6 = Sunday
    
    # Base congestion varies by city (20-60%)
    base_congestion = (seed % 40) + 20
    
    # Rush hour multiplier (7-10 AM: 1.5x, 5-8 PM: 1.6x)
    if 7 <= hour <= 10:
        rush_factor = 1.5
    elif 17 <= hour <= 20:
        rush_factor = 1.6
    elif 11 <= hour <= 16:
        rush_factor = 1.2  # Moderate daytime traffic
    else:
        rush_factor = 0.8  # Night time - less traffic
    
    # Weekend factor (reduce by 30% on weekends)
    weekend_factor = 0.7 if day_of_week >= 5 else 1.0
    
    # City-specific factors
    city_factors = {
        "Mumbai": 1.3,      # Historically high traffic
        "Delhi": 1.25,      # High traffic
        "Bengaluru": 1.4,   # Notorious traffic
        "Chennai": 1.1,
        "Pune": 1.15,
        "Hyderabad": 1.1,
        "Kolkata": 1.2,
        "Ahmedabad": 1.05,
        "Jaipur": 1.0,
        "Lucknow": 0.95
    }
    
    city_factor = city_factors.get(city, 1.0)
    
    # Calculate final congestion
    congestion = base_congestion * rush_factor * weekend_factor * city_factor
    congestion = min(congestion, 100)
    congestion = round(congestion, 1)
    
    # Calculate simulated speeds
    free_flow_speed = 50  # Assumed free flow speed in km/h
    speed_reduction = congestion / 100
    current_speed = round(free_flow_speed * (1 - speed_reduction), 1)
    
    logger.info(
        f"🤖 Simulation for {city}: {congestion}% "
        f"(Hour: {hour}, Weekend: {day_of_week >= 5})"
    )
    
    return congestion, "AI Prediction Model", current_speed, free_flow_speed


def get_congestion_for_cities(city_coords, tomtom_key, mapmyindia_key=""):
    """
    Get traffic congestion for all cities with fallback logic
    
    Args:
        city_coords: Dictionary of city names to (lat, lon) tuples
        tomtom_key: TomTom API key
        mapmyindia_key: MapmyIndia API key (optional)
        
    Returns:
        tuple: (results_list, api_working_bool, api_source_string)
    """
    results = []
    api_working = False
    api_source = "None"
    
    logger.info("="*70)
    logger.info("🚀 STARTING TRAFFIC DATA COLLECTION")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🔑 TomTom Key: {'✅ Available' if tomtom_key else '❌ Missing'}")
    logger.info(f"🔑 MapmyIndia Key: {'✅ Available' if mapmyindia_key else '❌ Missing'}")
    logger.info("="*70)
    
    for city, (lat, lon) in city_coords.items():
        logger.info(f"\n{'='*70}")
        logger.info(f"📍 Processing: {city} ({lat:.4f}, {lon:.4f})")
        logger.info(f"{'='*70}")
        
        congestion = None
        source = "Unknown"
        current_speed = "N/A"
        free_flow_speed = "N/A"
        
        # Try TomTom first (most reliable)
        if tomtom_key:
            congestion, source, current_speed, free_flow_speed = get_traffic_from_tomtom(
                lat, lon, tomtom_key
            )
            
            if congestion is not None and "API" in source:
                api_working = True
                api_source = "TomTom Traffic API"
        
        # Try MapmyIndia as backup
        if congestion is None and mapmyindia_key:
            logger.info("🔄 Trying MapmyIndia fallback...")
            congestion, source, current_speed, free_flow_speed = get_traffic_from_mapmyindia(
                lat, lon, mapmyindia_key
            )
            
            if congestion is not None and "API" in source:
                api_working = True
                api_source = "MapmyIndia Route API"
        
        # Fallback to simulation
        if congestion is None:
            logger.warning("⚠️ All APIs failed, using simulation")
            congestion, source, current_speed, free_flow_speed = get_simulated_congestion(
                city, lat, lon
            )
        
        # Add to results
        results.append({
            "city": city,
            "lat": lat,
            "lon": lon,
            "congestion": congestion,
            "source": source,
            "current_speed": current_speed,
            "free_flow_speed": free_flow_speed,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"✅ {city} Result: {congestion}% from {source}")
    
    # Final summary
    logger.info("\n" + "="*70)
    logger.info("📊 COLLECTION COMPLETE")
    logger.info(f"{'✅ SUCCESS - Using Real API Data' if api_working else '❌ API UNAVAILABLE - Using Simulation'}")
    if api_working:
        logger.info(f"🌐 Active Source: {api_source}")
    logger.info(f"📈 Total Cities Processed: {len(results)}")
    logger.info("="*70 + "\n")
    
    return results, api_working, api_source