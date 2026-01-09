#!/usr/bin/env python3
"""
Build comprehensive US cities database from free government data.
Downloads and processes US Census Gazetteer files.

Output: execution/us_cities.json (all 50 states, ~20,000+ cities)
"""

import json
import csv
import urllib.request
import zipfile
import io

def download_census_cities():
    """
    Download US Census 2023 Gazetteer Place Files (all incorporated cities).
    FREE government data - no API key needed.
    """
    print("📥 Downloading US Census city data (FREE)...")

    url = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_place_national.zip"

    try:
        response = urllib.request.urlopen(url, timeout=120)
        zip_data = io.BytesIO(response.read())

        with zipfile.ZipFile(zip_data) as z:
            # Extract the TXT file
            txt_file = [f for f in z.namelist() if f.endswith('.txt')][0]
            with z.open(txt_file) as f:
                content = f.read().decode('latin-1')

        print("✅ Download complete!")
        return content

    except Exception as e:
        print(f"❌ Download failed: {e}")
        print("⚠️  Using fallback: manual curated database")
        return None


def parse_census_data(content):
    """Parse Census gazetteer format into city database."""
    cities = {}

    lines = content.strip().split('\n')
    header = lines[0].split('\t')

    for line in lines[1:]:
        fields = line.split('\t')
        if len(fields) < 6:
            continue

        try:
            state_abbr = fields[0]  # USPS state code
            name = fields[3]  # Place name
            lat = float(fields[5])  # INTPTLAT
            lon = float(fields[6])  # INTPTLONG

            # Create key: "City, ST"
            city_key = f"{name}, {state_abbr}"

            cities[city_key] = {
                "lat": lat,
                "lon": lon,
                "state": state_abbr
            }
        except:
            continue

    return cities


def create_manual_database():
    """
    Fallback: Manually curated database of top US cities.
    Covers all 50 states + DC with major metropolitan areas.
    """
    print("📝 Creating curated US cities database...")

    # This will be expanded - for now returning comprehensive NJ + major US cities
    cities = {}

    # Import the existing manual database (we'll expand this)
    exec(open('execution/us_cities.json').read(), {'cities': cities})

    return cities


def main():
    """Build the US cities database."""

    # Try Census data first (most comprehensive)
    census_data = download_census_cities()

    if census_data:
        cities = parse_census_data(census_data)
        print(f"✅ Processed {len(cities)} cities from US Census")
    else:
        # Fallback to manual database
        with open('execution/us_cities.json', 'r') as f:
            cities = json.load(f)
        print(f"✅ Using manual database: {len(cities)} cities")

    # Save
    output_path = 'execution/us_cities.json'
    with open(output_path, 'w') as f:
        json.dump(cities, f, indent=2)

    # Stats
    states = set(c['state'] for c in cities.values())
    print(f"\n📊 Database Stats:")
    print(f"   Total cities: {len(cities)}")
    print(f"   States covered: {len(states)}")
    print(f"   Saved to: {output_path}")

    # Show sample
    print(f"\n📍 Sample cities:")
    for city in list(cities.keys())[:10]:
        print(f"   - {city}")


if __name__ == "__main__":
    main()
