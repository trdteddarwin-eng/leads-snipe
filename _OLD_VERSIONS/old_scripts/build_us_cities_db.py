#!/usr/bin/env python3
"""
Build US Cities Database from Census Data

Downloads and processes US Census Bureau city coordinate data
to create a searchable database for all 50 states.

Output: execution/us_cities.json
"""

import json
import urllib.request
import zipfile
import io
import csv

def download_and_process_census_data():
    """Download US Census city data and convert to JSON."""

    print("📥 Downloading US Census city database...")
    url = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_place_national.zip"

    # Download zip file
    response = urllib.request.urlopen(url)
    zip_data = response.read()

    print("📦 Extracting data...")
    # Extract TSV file from zip
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        # Find the .txt file
        txt_files = [f for f in z.namelist() if f.endswith('.txt')]
        if not txt_files:
            print("❌ No .txt file found in zip")
            return None

        txt_file = txt_files[0]
        with z.open(txt_file) as f:
            content = f.read().decode('latin-1')

    print(f"✅ Processing {txt_file}...")

    # Parse TSV data
    cities = {}
    reader = csv.DictReader(io.StringIO(content), delimiter='\t')

    state_abbrev = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
        'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
        'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
        'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
        'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
        'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
        'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
        'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
        'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
        'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
        'Wisconsin': 'WI', 'Wyoming': 'WY', 'District of Columbia': 'DC',
        'Puerto Rico': 'PR'
    }

    count = 0
    for row in reader:
        try:
            # Get city name and state
            city_name = row.get('NAME', '').strip()
            state_name = row.get('USPS', '').strip()  # State abbreviation

            if not city_name or not state_name:
                continue

            # Remove city type suffix (CDP, city, town, etc.)
            city_name_clean = city_name.replace(' CDP', '').replace(' city', '').replace(' town', '').replace(' village', '').replace(' borough', '')

            # Get coordinates
            lat = float(row.get('INTPTLAT', 0))
            lon = float(row.get('INTPTLONG', 0))

            if lat == 0 or lon == 0:
                continue

            # Create key
            city_key = f"{city_name_clean}, {state_name}"

            cities[city_key] = {
                "lat": lat,
                "lon": lon,
                "state": state_name,
                "full_name": city_name  # Keep original with type
            }

            count += 1
            if count % 1000 == 0:
                print(f"   Processed {count} cities...")

        except (ValueError, KeyError) as e:
            continue

    return cities


def main():
    print("🇺🇸 Building US Cities Database\n")

    cities = download_and_process_census_data()

    if not cities:
        print("❌ Failed to build database")
        return

    # Save to JSON
    output_path = 'execution/us_cities.json'
    with open(output_path, 'w') as f:
        json.dump(cities, f, indent=2)

    print(f"\n✅ Success!")
    print(f"   Cities: {len(cities):,}")
    print(f"   File: {output_path}")
    print(f"   Size: {len(json.dumps(cities)) / 1024 / 1024:.1f} MB")

    # Show sample
    print("\n📊 Sample cities:")
    for i, (city, data) in enumerate(list(cities.items())[:10], 1):
        print(f"   {i}. {city} - ({data['lat']:.4f}, {data['lon']:.4f})")


if __name__ == "__main__":
    main()
