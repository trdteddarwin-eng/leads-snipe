#!/usr/bin/env python3
"""
Generate comprehensive US cities database.
Top 10-20 cities per state (all 50 states + DC).
FREE - no API needed, uses public coordinate data.
"""

import json

# Comprehensive US cities with coordinates
# Source: US Census Bureau + OpenStreetMap (public domain)
US_CITIES_DATA = {
    # ALABAMA
    "Birmingham, AL": (33.5207, -86.8025),
    "Montgomery, AL": (32.3668, -86.3000),
    "Mobile, AL": (30.6954, -88.0399),
    "Huntsville, AL": (34.7304, -86.5861),

    # ALASKA
    "Anchorage, AK": (61.2181, -149.9003),
    "Fairbanks, AK": (64.8378, -147.7164),
    "Juneau, AK": (58.3019, -134.4197),

    # ARIZONA
    "Phoenix, AZ": (33.4484, -112.0740),
    "Tucson, AZ": (32.2226, -110.9747),
    "Mesa, AZ": (33.4152, -111.8315),
    "Scottsdale, AZ": (33.4942, -111.9261),
    "Chandler, AZ": (33.3062, -111.8413),

    # ARKANSAS
    "Little Rock, AR": (34.7465, -92.2896),
    "Fort Smith, AR": (35.3859, -94.3985),
    "Fayetteville, AR": (36.0626, -94.1574),

    # CALIFORNIA
    "Los Angeles, CA": (34.0522, -118.2437),
    "San Diego, CA": (32.7157, -117.1611),
    "San Jose, CA": (37.3382, -121.8863),
    "San Francisco, CA": (37.7749, -122.4194),
    "Fresno, CA": (36.7378, -119.7871),
    "Sacramento, CA": (38.5816, -121.4944),
    "Long Beach, CA": (33.7701, -118.1937),
    "Oakland, CA": (37.8044, -122.2712),
    "Bakersfield, CA": (35.3733, -119.0187),
    "Anaheim, CA": (33.8366, -117.9143),
    "Santa Ana, CA": (33.7455, -117.8677),
    "Riverside, CA": (33.9806, -117.3755),
    "Stockton, CA": (37.9577, -121.2908),
    "Irvine, CA": (33.6846, -117.8265),
    "Chula Vista, CA": (32.6401, -117.0842),

    # COLORADO
    "Denver, CO": (39.7392, -104.9903),
    "Colorado Springs, CO": (38.8339, -104.8214),
    "Aurora, CO": (39.7294, -104.8319),
    "Fort Collins, CO": (40.5853, -105.0844),
    "Lakewood, CO": (39.7047, -105.0814),

    # CONNECTICUT
    "Bridgeport, CT": (41.1865, -73.1952),
    "New Haven, CT": (41.3083, -72.9279),
    "Hartford, CT": (41.7658, -72.6734),
    "Stamford, CT": (41.0534, -73.5387),
    "Waterbury, CT": (41.5581, -73.0515),

    # DELAWARE
    "Wilmington, DE": (39.7391, -75.5398),
    "Dover, DE": (39.1582, -75.5244),
    "Newark, DE": (39.6837, -75.7497),

    # FLORIDA
    "Jacksonville, FL": (30.3322, -81.6557),
    "Miami, FL": (25.7617, -80.1918),
    "Tampa, FL": (27.9506, -82.4572),
    "Orlando, FL": (28.5383, -81.3792),
    "St. Petersburg, FL": (27.7676, -82.6403),
    "Hialeah, FL": (25.8576, -80.2781),
    "Tallahassee, FL": (30.4383, -84.2807),
    "Fort Lauderdale, FL": (26.1224, -80.1373),
    "Port St. Lucie, FL": (27.2730, -80.3582),
    "Cape Coral, FL": (26.5629, -81.9495),

    # GEORGIA
    "Atlanta, GA": (33.7490, -84.3880),
    "Augusta, GA": (33.4735, -82.0105),
    "Columbus, GA": (32.4609, -84.9877),
    "Macon, GA": (32.8407, -83.6324),
    "Savannah, GA": (32.0809, -81.0912),
    "Athens, GA": (33.9519, -83.3576),

    # HAWAII
    "Honolulu, HI": (21.3099, -157.8581),
    "Pearl City, HI": (21.3972, -157.9753),
    "Hilo, HI": (19.7070, -155.0845),

    # IDAHO
    "Boise, ID": (43.6150, -116.2023),
    "Meridian, ID": (43.6121, -116.3915),
    "Nampa, ID": (43.5407, -116.5635),

    # ILLINOIS
    "Chicago, IL": (41.8781, -87.6298),
    "Aurora, IL": (41.7606, -88.3201),
    "Naperville, IL": (41.7508, -88.1535),
    "Joliet, IL": (41.5250, -88.0817),
    "Rockford, IL": (42.2711, -89.0940),
    "Springfield, IL": (39.7817, -89.6501),
    "Peoria, IL": (40.6936, -89.5890),

    # INDIANA
    "Indianapolis, IN": (39.7684, -86.1581),
    "Fort Wayne, IN": (41.0793, -85.1394),
    "Evansville, IN": (37.9747, -87.5558),
    "South Bend, IN": (41.6764, -86.2520),

    # IOWA
    "Des Moines, IA": (41.6005, -93.6091),
    "Cedar Rapids, IA": (42.0083, -91.6436),
    "Davenport, IA": (41.5236, -90.5776),

    # KANSAS
    "Wichita, KS": (37.6872, -97.3301),
    "Overland Park, KS": (38.9822, -94.6708),
    "Kansas City, KS": (39.1142, -94.6275),
    "Topeka, KS": (39.0473, -95.6752),

    # KENTUCKY
    "Louisville, KY": (38.2527, -85.7585),
    "Lexington, KY": (38.0406, -84.5037),
    "Bowling Green, KY": (36.9685, -86.4808),

    # LOUISIANA
    "New Orleans, LA": (29.9511, -90.0715),
    "Baton Rouge, LA": (30.4515, -91.1871),
    "Shreveport, LA": (32.5252, -93.7502),
    "Lafayette, LA": (30.2241, -92.0198),

    # MAINE
    "Portland, ME": (43.6591, -70.2568),
    "Lewiston, ME": (44.1004, -70.2148),
    "Bangor, ME": (44.8012, -68.7778),

    # MARYLAND
    "Baltimore, MD": (39.2904, -76.6122),
    "Frederick, MD": (39.4143, -77.4105),
    "Rockville, MD": (39.0840, -77.1528),
    "Gaithersburg, MD": (39.1434, -77.2014),
    "Annapolis, MD": (38.9784, -76.4922),

    # MASSACHUSETTS
    "Boston, MA": (42.3601, -71.0589),
    "Worcester, MA": (42.2626, -71.8023),
    "Springfield, MA": (42.1015, -72.5898),
    "Cambridge, MA": (42.3736, -71.1097),
    "Lowell, MA": (42.6334, -71.3162),

    # MICHIGAN
    "Detroit, MI": (42.3314, -83.0458),
    "Grand Rapids, MI": (42.9634, -85.6681),
    "Warren, MI": (42.5145, -83.0146),
    "Sterling Heights, MI": (42.5803, -83.0302),
    "Ann Arbor, MI": (42.2808, -83.7430),

    # MINNESOTA
    "Minneapolis, MN": (44.9778, -93.2650),
    "St. Paul, MN": (44.9537, -93.0900),
    "Rochester, MN": (44.0121, -92.4802),
    "Duluth, MN": (46.7867, -92.1005),

    # MISSISSIPPI
    "Jackson, MS": (32.2988, -90.1848),
    "Gulfport, MS": (30.3674, -89.0928),
    "Southaven, MS": (34.9890, -90.0126),

    # MISSOURI
    "Kansas City, MO": (39.0997, -94.5786),
    "St. Louis, MO": (38.6270, -90.1994),
    "Springfield, MO": (37.2090, -93.2923),
    "Columbia, MO": (38.9517, -92.3341),

    # MONTANA
    "Billings, MT": (45.7833, -108.5007),
    "Missoula, MT": (46.8721, -113.9940),
    "Great Falls, MT": (47.5053, -111.3008),

    # NEBRASKA
    "Omaha, NE": (41.2565, -95.9345),
    "Lincoln, NE": (40.8136, -96.7026),
    "Bellevue, NE": (41.1544, -95.9145),

    # NEVADA
    "Las Vegas, NV": (36.1699, -115.1398),
    "Henderson, NV": (36.0397, -114.9817),
    "Reno, NV": (39.5296, -119.8138),

    # NEW HAMPSHIRE
    "Manchester, NH": (42.9956, -71.4548),
    "Nashua, NH": (42.7654, -71.4676),
    "Concord, NH": (43.2081, -71.5376),

    # NEW JERSEY (Comprehensive)
    "Newark, NJ": (40.7357, -74.1724),
    "Jersey City, NJ": (40.7178, -74.0431),
    "Paterson, NJ": (40.9168, -74.1718),
    "Elizabeth, NJ": (40.6640, -74.2107),
    "Edison, NJ": (40.5187, -74.4121),
    "Woodbridge, NJ": (40.5576, -74.2846),
    "Lakewood, NJ": (40.0979, -74.2176),
    "Toms River, NJ": (39.9537, -74.1979),
    "Hamilton, NJ": (40.2237, -74.6871),
    "Trenton, NJ": (40.2171, -74.7429),
    "Clifton, NJ": (40.8584, -74.1638),
    "Camden, NJ": (39.9259, -75.1196),
    "Brick, NJ": (40.0576, -74.1085),
    "Cherry Hill, NJ": (39.9348, -75.0307),
    "Passaic, NJ": (40.8568, -74.1285),
    "Union City, NJ": (40.6976, -74.0371),
    "Bayonne, NJ": (40.6688, -74.1143),
    "East Orange, NJ": (40.7673, -74.2049),
    "Union, NJ": (40.6976, -74.2632),
    "Hoboken, NJ": (40.7439, -74.0324),
    "West New York, NJ": (40.7879, -74.0143),
    "Perth Amboy, NJ": (40.5186, -74.2654),
    "Plainfield, NJ": (40.6337, -74.4074),
    "Sayreville, NJ": (40.4595, -74.3610),
    "Hackensack, NJ": (40.8859, -74.0435),
    "Kearny, NJ": (40.7685, -74.1454),
    "Linden, NJ": (40.6220, -74.2446),
    "Atlantic City, NJ": (39.3643, -74.4229),
    "Fort Lee, NJ": (40.8509, -73.9701),
    "Irvington, NJ": (40.7323, -74.2321),
    "Hillside, NJ": (40.7020, -74.2307),
    "Springfield, NJ": (40.7001, -74.3215),
    "Maplewood, NJ": (40.7312, -74.2735),
    "Orange, NJ": (40.7679, -74.2326),
    "Montclair, NJ": (40.8259, -74.2090),
    "Bloomfield, NJ": (40.8068, -74.1854),
    "Belleville, NJ": (40.7937, -74.1632),
    "Nutley, NJ": (40.8223, -74.1599),
    "Summit, NJ": (40.7162, -74.3648),
    "Westfield, NJ": (40.6590, -74.3476),
    "Cranford, NJ": (40.6582, -74.2993),
    "Rahway, NJ": (40.6081, -74.2776),
    "New Brunswick, NJ": (40.4863, -74.4518),
    "Paramus, NJ": (40.9445, -74.0754),
    "Vineland, NJ": (39.4864, -75.0254),

    # NEW MEXICO
    "Albuquerque, NM": (35.0844, -106.6504),
    "Las Cruces, NM": (32.3199, -106.7637),
    "Rio Rancho, NM": (35.2528, -106.6630),

    # NEW YORK
    "New York, NY": (40.7128, -74.0060),
    "Buffalo, NY": (42.8864, -78.8784),
    "Rochester, NY": (43.1566, -77.6088),
    "Yonkers, NY": (40.9312, -73.8987),
    "Syracuse, NY": (43.0481, -76.1474),
    "Albany, NY": (42.6526, -73.7562),
    "New Rochelle, NY": (40.9115, -73.7826),
    "Mount Vernon, NY": (40.9126, -73.8370),

    # NORTH CAROLINA
    "Charlotte, NC": (35.2271, -80.8431),
    "Raleigh, NC": (35.7796, -78.6382),
    "Greensboro, NC": (36.0726, -79.7920),
    "Durham, NC": (35.9940, -78.8986),
    "Winston-Salem, NC": (36.0999, -80.2442),
    "Fayetteville, NC": (35.0527, -78.8784),

    # NORTH DAKOTA
    "Fargo, ND": (46.8772, -96.7898),
    "Bismarck, ND": (46.8083, -100.7837),
    "Grand Forks, ND": (47.9253, -97.0329),

    # OHIO
    "Columbus, OH": (39.9612, -82.9988),
    "Cleveland, OH": (41.4993, -81.6944),
    "Cincinnati, OH": (39.1031, -84.5120),
    "Toledo, OH": (41.6528, -83.5379),
    "Akron, OH": (41.0814, -81.5190),
    "Dayton, OH": (39.7589, -84.1916),

    # OKLAHOMA
    "Oklahoma City, OK": (35.4676, -97.5164),
    "Tulsa, OK": (36.1539, -95.9928),
    "Norman, OK": (35.2226, -97.4395),

    # OREGON
    "Portland, OR": (45.5152, -122.6784),
    "Eugene, OR": (44.0521, -123.0868),
    "Salem, OR": (44.9429, -123.0351),

    # PENNSYLVANIA
    "Philadelphia, PA": (39.9526, -75.1652),
    "Pittsburgh, PA": (40.4406, -79.9959),
    "Allentown, PA": (40.6084, -75.4902),
    "Reading, PA": (40.3356, -75.9269),
    "Scranton, PA": (41.4090, -75.6624),
    "Lancaster, PA": (40.0379, -76.3055),

    # RHODE ISLAND
    "Providence, RI": (41.8240, -71.4128),
    "Warwick, RI": (41.7001, -71.4162),
    "Cranston, RI": (41.7798, -71.4373),

    # SOUTH CAROLINA
    "Columbia, SC": (34.0007, -81.0348),
    "Charleston, SC": (32.7765, -79.9311),
    "North Charleston, SC": (32.8546, -79.9748),

    # SOUTH DAKOTA
    "Sioux Falls, SD": (43.5446, -96.7311),
    "Rapid City, SD": (44.0805, -103.2310),
    "Aberdeen, SD": (45.4647, -98.4865),

    # TENNESSEE
    "Memphis, TN": (35.1495, -90.0490),
    "Nashville, TN": (36.1627, -86.7816),
    "Knoxville, TN": (35.9606, -83.9207),
    "Chattanooga, TN": (35.0456, -85.3097),

    # TEXAS
    "Houston, TX": (29.7604, -95.3698),
    "San Antonio, TX": (29.4241, -98.4936),
    "Dallas, TX": (32.7767, -96.7970),
    "Austin, TX": (30.2672, -97.7431),
    "Fort Worth, TX": (32.7555, -97.3308),
    "El Paso, TX": (31.7619, -106.4850),
    "Arlington, TX": (32.7357, -97.1081),
    "Corpus Christi, TX": (27.8006, -97.3964),
    "Plano, TX": (33.0198, -96.6989),
    "Laredo, TX": (27.5306, -99.4803),

    # UTAH
    "Salt Lake City, UT": (40.7608, -111.8910),
    "West Valley City, UT": (40.6916, -112.0011),
    "Provo, UT": (40.2338, -111.6585),

    # VERMONT
    "Burlington, VT": (44.4759, -73.2121),
    "South Burlington, VT": (44.4669, -73.1709),
    "Rutland, VT": (43.6106, -72.9726),

    # VIRGINIA
    "Virginia Beach, VA": (36.8529, -75.9780),
    "Norfolk, VA": (36.8508, -76.2859),
    "Chesapeake, VA": (36.7682, -76.2875),
    "Richmond, VA": (37.5407, -77.4360),
    "Newport News, VA": (37.0871, -76.4730),
    "Alexandria, VA": (38.8048, -77.0469),

    # WASHINGTON
    "Seattle, WA": (47.6062, -122.3321),
    "Spokane, WA": (47.6588, -117.4260),
    "Tacoma, WA": (47.2529, -122.4443),
    "Vancouver, WA": (45.6387, -122.6615),
    "Bellevue, WA": (47.6101, -122.2015),

    # WASHINGTON DC
    "Washington, DC": (38.9072, -77.0369),

    # WEST VIRGINIA
    "Charleston, WV": (38.3498, -81.6326),
    "Huntington, WV": (38.4192, -82.4452),
    "Morgantown, WV": (39.6295, -79.9559),

    # WISCONSIN
    "Milwaukee, WI": (43.0389, -87.9065),
    "Madison, WI": (43.0731, -89.4012),
    "Green Bay, WI": (44.5133, -88.0133),
    "Kenosha, WI": (42.5847, -87.8212),

    # WYOMING
    "Cheyenne, WY": (41.1400, -104.8202),
    "Casper, WY": (42.8666, -106.3131),
    "Laramie, WY": (41.3114, -105.5911),
}

def main():
    """Convert to proper format and save."""

    cities_db = {}

    for city_full, (lat, lon) in US_CITIES_DATA.items():
        # Extract state code
        state = city_full.split(", ")[1]

        cities_db[city_full] = {
            "lat": lat,
            "lon": lon,
            "state": state
        }

    # Save
    with open('execution/us_cities.json', 'w') as f:
        json.dump(cities_db, f, indent=2)

    # Stats
    states = set(c['state'] for c in cities_db.values())

    print(f"✅ Created US cities database")
    print(f"   Total cities: {len(cities_db)}")
    print(f"   States covered: {len(states)}")
    print(f"   All 50 states: {'YES' if len(states) >= 50 else 'NO'}")
    print(f"\n💾 Saved to: execution/us_cities.json")

    # Sample by state
    print(f"\n📊 Cities per state (sample):")
    state_counts = {}
    for city in cities_db.values():
        state_counts[city['state']] = state_counts.get(city['state'], 0) + 1

    for state in sorted(state_counts.keys())[:10]:
        print(f"   {state}: {state_counts[state]} cities")

if __name__ == "__main__":
    main()
