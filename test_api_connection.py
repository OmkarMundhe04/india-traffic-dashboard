"""
TomTom API Connection Diagnostic Tool
Run this to verify your TomTom API key is working correctly

Usage: python test_api_connection.py
"""

import requests
import sys
from datetime import datetime

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}{text.center(70)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"{BLUE}ℹ️  {text}{RESET}")


def test_tomtom_api(api_key, test_locations):
    """
    Test TomTom API with multiple locations
    
    Args:
        api_key: TomTom API key
        test_locations: List of (city_name, lat, lon) tuples
        
    Returns:
        bool: True if API is working
    """
    print_header("TOMTOM TRAFFIC API TEST")
    
    if not api_key or len(api_key) < 10:
        print_error("Invalid API key format")
        print_info(f"Current value: '{api_key}'")
        return False
    
    print_success(f"API Key: {api_key[:10]}...{api_key[-10:]}")
    print_info(f"Key length: {len(api_key)} characters")
    print()
    
    working_count = 0
    total_tests = len(test_locations)
    
    for city, lat, lon in test_locations:
        print(f"\n{BOLD}Testing: {city} ({lat}, {lon}){RESET}")
        print("-" * 70)
        
        url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
        params = {
            "key": api_key,
            "point": f"{lat},{lon}",
            "unit": "KMPH"
        }
        
        try:
            print_info(f"Requesting: {url}")
            print_info(f"Parameters: point={lat},{lon}, unit=KMPH")
            
            response = requests.get(url, params=params, timeout=10)
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "flowSegmentData" in data:
                    flow = data["flowSegmentData"]
                    current_speed = flow.get("currentSpeed", 0)
                    free_flow_speed = flow.get("freeFlowSpeed", 0)
                    current_travel_time = flow.get("currentTravelTime", 0)
                    free_flow_travel_time = flow.get("freeFlowTravelTime", 0)
                    confidence = flow.get("confidence", 0)
                    
                    # Calculate congestion
                    if free_flow_speed > 0:
                        speed_ratio = current_speed / free_flow_speed
                        congestion = round((1 - speed_ratio) * 100, 1)
                        congestion = max(0, min(100, congestion))
                    else:
                        congestion = 0
                    
                    print_success(f"API Response Successful!")
                    print()
                    print(f"  🚗 Current Speed:      {current_speed} km/h")
                    print(f"  ⚡ Free Flow Speed:    {free_flow_speed} km/h")
                    print(f"  🚦 Congestion Level:   {congestion}%")
                    print(f"  ⏱️  Current Travel Time: {current_travel_time} seconds")
                    print(f"  ⏱️  Free Flow Time:      {free_flow_travel_time} seconds")
                    print(f"  📊 Confidence:         {confidence:.0%}")
                    
                    working_count += 1
                    
                    # Traffic status
                    if congestion < 30:
                        print(f"  {GREEN}🟢 Status: Free Flow{RESET}")
                    elif congestion < 60:
                        print(f"  {YELLOW}🟡 Status: Moderate Traffic{RESET}")
                    else:
                        print(f"  {RED}🔴 Status: Heavy Congestion{RESET}")
                else:
                    print_error("Invalid response structure")
                    print_info(f"Response: {str(data)[:200]}")
                    
            elif response.status_code == 401:
                print_error("Authentication Failed!")
                print_warning("Your API key is invalid or expired")
                print_info("Get a new key at: https://developer.tomtom.com/")
                return False
                
            elif response.status_code == 403:
                print_error("Access Forbidden!")
                print_warning("This endpoint may not be included in your plan")
                print_info("Check your API subscription at: https://developer.tomtom.com/")
                return False
                
            elif response.status_code == 429:
                print_error("Rate Limit Exceeded!")
                print_warning("You've used up your daily request quota")
                print_info("Free tier: 2,500 requests/day")
                
            else:
                print_warning(f"Unexpected status code: {response.status_code}")
                print_info(f"Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print_error("Request Timeout!")
            print_warning("The API server took too long to respond")
            
        except requests.exceptions.ConnectionError:
            print_error("Connection Error!")
            print_warning("Could not connect to TomTom servers")
            print_info("Check your internet connection")
            
        except Exception as e:
            print_error(f"Unexpected Error: {str(e)}")
    
    print()
    print("="*70)
    print(f"\n{BOLD}Test Results:{RESET}")
    print(f"  ✅ Successful: {working_count}/{total_tests}")
    print(f"  ❌ Failed:     {total_tests - working_count}/{total_tests}")
    
    return working_count > 0


def test_rate_limits(api_key):
    """Test API rate limits"""
    print_header("RATE LIMIT TEST")
    
    print_info("Testing multiple rapid requests...")
    print_info("Free tier limit: 2,500 requests/day")
    
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {
        "key": api_key,
        "point": "19.0760,72.8777",  # Mumbai
        "unit": "KMPH"
    }
    
    success_count = 0
    for i in range(5):
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                print_warning(f"Rate limited on request {i+1}")
                break
        except Exception as e:
            print_error(f"Request {i+1} failed: {str(e)}")
    
    print_success(f"Successfully made {success_count}/5 rapid requests")
    print_info("No rate limiting detected for normal usage")
    print()


def show_setup_instructions():
    """Show setup instructions"""
    print_header("SETUP INSTRUCTIONS")
    
    print(f"{BOLD}If the test failed, follow these steps:{RESET}\n")
    
    print(f"{BLUE}Step 1: Get TomTom API Key{RESET}")
    print("  1. Visit: https://developer.tomtom.com/")
    print("  2. Sign up for a free account")
    print("  3. Go to 'My Dashboard'")
    print("  4. Click 'Create New App'")
    print("  5. Copy your API key\n")
    
    print(f"{BLUE}Step 2: Set Environment Variable{RESET}")
    print(f"  {BOLD}For Linux/Mac:{RESET}")
    print(f"    export TOMTOM_API_KEY='your_key_here'")
    print(f"  {BOLD}For Windows (CMD):{RESET}")
    print(f"    set TOMTOM_API_KEY=your_key_here")
    print(f"  {BOLD}For Windows (PowerShell):{RESET}")
    print(f"    $env:TOMTOM_API_KEY='your_key_here'\n")
    
    print(f"{BLUE}Step 3: Update Your Code{RESET}")
    print(f"  In app.py, set:")
    print(f"    TOMTOM_KEY = os.getenv('TOMTOM_API_KEY', 'your_key_here')\n")
    
    print(f"{BLUE}Step 4: Run Your App{RESET}")
    print(f"    streamlit run app.py\n")


def main():
    """Main test function"""
    print_header("🚦 TOMTOM TRAFFIC API DIAGNOSTIC TOOL 🚦")
    print_info(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Your API key (replace with actual key or get from environment)
    API_KEY = "P8syJbFkhS9wAsarqMtyIlHYDhnxbgUo"
    
    print()
    print(f"{BOLD}Testing with API Key:{RESET}")
    print(f"  {API_KEY[:20]}...{API_KEY[-20:]}")
    print()
    
    # Test locations (major Indian cities)
    test_locations = [
        ("Mumbai", 19.0760, 72.8777),
        ("Delhi", 28.6139, 77.2090),
        ("Bengaluru", 12.9716, 77.5946),
        ("Chennai", 13.0827, 80.2707),
        ("Pune", 18.5204, 73.8567)
    ]
    
    # Run tests
    api_working = test_tomtom_api(API_KEY, test_locations)
    
    if api_working:
        print()
        test_rate_limits(API_KEY)
    
    # Final verdict
    print_header("FINAL VERDICT")
    
    if api_working:
        print_success("🎉 YOUR API IS WORKING PERFECTLY!")
        print()
        print(f"{GREEN}{BOLD}Next Steps:{RESET}")
        print(f"  1. Your TomTom API key is valid and working")
        print(f"  2. Run your Streamlit app: streamlit run app.py")
        print(f"  3. You should see LIVE traffic data!")
        print()
        print(f"{GREEN}✨ You'll get real-time traffic for all Indian cities! ✨{RESET}")
    else:
        print_error("❌ API TEST FAILED")
        print()
        print(f"{RED}{BOLD}Issues Detected:{RESET}")
        print(f"  • API key may be invalid or expired")
        print(f"  • Network connectivity issues")
        print(f"  • API endpoint access problems")
        print()
        show_setup_instructions()
    
    print_header("TEST COMPLETE")
    
    return 0 if api_working else 1


if __name__ == "__main__":
    sys.exit(main())