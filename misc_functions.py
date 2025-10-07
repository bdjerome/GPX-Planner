
#convert pace between min/km and min/mile
def convert_to_mph(pace_min_per_km):
    """Convert pace from min/km to min/mile"""
    return pace_min_per_km * 1.60934

def convert_to_kmh(pace_min_per_mile):
    """Convert pace from min/mile to min/km"""
    return pace_min_per_mile / 1.60934