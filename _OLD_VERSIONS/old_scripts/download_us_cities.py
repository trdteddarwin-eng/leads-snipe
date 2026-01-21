#!/usr/bin/env python3
import json, urllib.request, zipfile, io, csv

print("📥 Downloading US Census data...")
url = 'https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_place_national.zip'
response = urllib.request.urlopen(url)

print("📦 Extracting...")
with zipfile.ZipFile(io.BytesIO(response.read())) as z:
    txt_file = [f for f in z.namelist() if f.endswith('.txt')][0]
    with z.open(txt_file) as f:
        content = f.read().decode('latin-1')

print("🔨 Processing cities...")
reader = csv.DictReader(io.StringIO(content), delimiter='\t')
cities = {}

for i, row in enumerate(reader):
    try:
        row = {k.strip(): v.strip() for k, v in row.items()}
        name = row['NAME'].replace(' city', '').replace(' town', '').replace(' CDP', '').replace(' village', '').replace(' borough', '')
        state = row['USPS']
        lat, lon = float(row['INTPTLAT']), float(row['INTPTLONG'])
        cities[f'{name}, {state}'] = {'lat': lat, 'lon': lon, 'state': state}
        if (i+1) % 2000 == 0:
            print(f"  Processed {i+1} places...")
    except:
        pass

with open('execution/us_cities.json', 'w') as f:
    json.dump(cities, f, indent=2)
print(f"\n✅ Created database with {len(cities):,} cities")
print(f"📊 Sample cities:")
for city in list(cities.keys())[:5]:
    print(f"   - {city}")
