"""Generate a rich, realistic restaurant dataset for the CSV Q&A agent.

100 rows of Indian restaurant data across 8 cities with 11 columns.
"""

import csv
import random
from pathlib import Path

random.seed(42)

CITIES_AREAS = {
    "Bangalore": ["Koramangala", "Indiranagar", "HSR Layout", "Whitefield", "Jayanagar", "MG Road"],
    "Mumbai": ["Bandra", "Andheri", "Colaba", "Lower Parel", "Juhu", "Powai"],
    "Delhi": ["Connaught Place", "Hauz Khas", "Saket", "Chandni Chowk", "Karol Bagh", "Rajouri Garden"],
    "Chennai": ["T. Nagar", "Anna Nagar", "Adyar", "Velachery", "Mylapore", "Besant Nagar"],
    "Hyderabad": ["Banjara Hills", "Jubilee Hills", "Madhapur", "Gachibowli", "Begumpet", "Secunderabad"],
    "Pune": ["Koregaon Park", "Viman Nagar", "Hinjawadi", "FC Road", "Baner", "Kothrud"],
    "Kolkata": ["Park Street", "Salt Lake", "New Town", "Esplanade", "Gariahat", "Ballygunge"],
    "Jaipur": ["MI Road", "C-Scheme", "Malviya Nagar", "Vaishali Nagar", "Tonk Road", "Raja Park"],
}

CUISINES = [
    "North Indian", "South Indian", "Chinese", "Italian", "Mughlai",
    "Seafood", "Japanese", "Thai", "Cafe", "Street Food", "Continental",
    "Hyderabadi", "Bengali", "Rajasthani", "Mexican", "American",
    "BBQ", "Desserts", "Lebanese", "Korean",
]

RESTAURANT_TYPES = ["Dine-out", "Delivery", "Café", "Takeaway"]

FIRST_WORDS = [
    "Spice", "Royal", "Golden", "Silver", "Crystal", "Blue", "Green",
    "Urban", "Coastal", "Rustic", "Fresh", "Grand", "Little", "Classic",
    "Saffron", "Pepper", "Basil", "Mint", "Olive", "Ginger",
]

SECOND_WORDS = [
    "Garden", "Kitchen", "House", "Palace", "Corner", "Bistro", "Grill",
    "Café", "Express", "Hub", "Point", "Room", "Table", "Plate",
    "Bites", "Flavors", "Delights", "Lounge", "Junction", "Stop",
]

# Cuisine-specific well-known restaurant-style names
SPECIALTY_NAMES = [
    "Biryani Blues", "Curry House", "Tandoor Express", "Kebab King",
    "Dosa Corner", "Filter Coffee Co", "Haleem Hub", "Dragon Wok",
    "Sushi Zen", "Pizza Palace", "Burger Barn", "Noodle Bar",
    "Taco Town", "Ramen Room", "Thai Orchid", "Paneer Paradise",
    "Sambar Stories", "Chai Adda", "Paratha Point", "Wok This Way",
    "Momos Factory", "Dal Tadka", "Idli Street", "Shawarma Station",
    "Pho Republic", "Butter Story", "Masala Box", "Rice Bowl",
    "Tikka Junction", "Chaat Corner",
]


def _generate_name(index: int) -> str:
    """Generate a unique restaurant name."""
    if index < len(SPECIALTY_NAMES):
        return SPECIALTY_NAMES[index]
    first = random.choice(FIRST_WORDS)
    second = random.choice(SECOND_WORDS)
    return f"{first} {second}"


def _cost_for_cuisine(cuisine: str) -> int:
    """Return a realistic cost_for_two based on cuisine."""
    base = {
        "Street Food": (150, 350), "Cafe": (200, 500), "South Indian": (200, 600),
        "North Indian": (400, 1200), "Chinese": (350, 900), "Mughlai": (500, 1200),
        "Italian": (500, 2000), "Japanese": (800, 3000), "Thai": (600, 1800),
        "Seafood": (600, 2000), "Continental": (600, 2000), "Korean": (700, 2500),
        "Lebanese": (500, 1500), "Mexican": (400, 1200), "American": (400, 1500),
        "Hyderabadi": (350, 900), "Bengali": (300, 800), "Rajasthani": (400, 1000),
        "BBQ": (500, 1500), "Desserts": (150, 600),
    }
    low, high = base.get(cuisine, (300, 1000))
    return round(random.randint(low, high) / 50) * 50  # round to nearest 50


def _generate_row(index: int) -> tuple:
    """Generate one restaurant row."""
    city = random.choices(
        list(CITIES_AREAS.keys()),
        weights=[18, 18, 14, 12, 12, 10, 8, 8],  # More restaurants in bigger cities
        k=1,
    )[0]
    area = random.choice(CITIES_AREAS[city])
    cuisine = random.choice(CUISINES)
    name = _generate_name(index)
    rating = round(random.uniform(2.5, 4.9), 1)
    cost = _cost_for_cuisine(cuisine)
    votes = random.randint(50, 5000)
    online = random.choices(["Yes", "No"], weights=[75, 25], k=1)[0]
    book_table = random.choices(["Yes", "No"], weights=[40, 60], k=1)[0]
    rtype = random.choice(RESTAURANT_TYPES)

    # Cost category
    if cost <= 400:
        cost_cat = "Budget"
    elif cost <= 1000:
        cost_cat = "Mid-range"
    else:
        cost_cat = "Premium"

    # Date between Jan 2023 and Jul 2024
    month = random.randint(1, 19)  # 1-12 = 2023, 13-19 = 2024
    year = 2023 if month <= 12 else 2024
    m = month if month <= 12 else month - 12
    day = random.randint(1, 28)
    listed_date = f"{year}-{m:02d}-{day:02d}"

    return (name, city, area, cuisine, rtype, rating, cost, votes,
            online, book_table, cost_cat, listed_date)


COLUMNS = [
    "name", "city", "area", "cuisine", "restaurant_type",
    "rating", "cost_for_two", "votes", "online_order",
    "book_table", "cost_category", "listed_date",
]


def main() -> None:
    out = Path(__file__).parent / "sample_data" / "dataset.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    used_names: set[str] = set()
    rows: list[tuple] = []

    for i in range(100):
        row = _generate_row(i)
        # Ensure unique names
        while row[0] in used_names:
            row = list(row)
            row[0] = f"{random.choice(FIRST_WORDS)} {random.choice(SECOND_WORDS)} {random.randint(2, 9)}"
            row = tuple(row)
        used_names.add(row[0])
        rows.append(row)

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
