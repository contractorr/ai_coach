from __future__ import annotations

import unicodedata
from pathlib import Path

GUIDE_ROOT = Path("content/curriculum/39-world-geography-fundamentals-guide")


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def _roster_countries(filename: str) -> set[str]:
    text = (GUIDE_ROOT / filename).read_text(encoding="utf-8")
    roster = text.split("## Complete regional roster", 1)[1].split("## Summary", 1)[0]
    countries: set[str] = set()
    for line in roster.splitlines():
        if (
            line.startswith("| ")
            and not line.startswith("| Country |")
            and not line.startswith("| ---")
        ):
            countries.add(_normalize(line.strip().split("|")[1].strip()))
    return countries


def _map_block(filename: str) -> str:
    text = (GUIDE_ROOT / filename).read_text(encoding="utf-8")
    start = text.index("```map") + len("```map")
    end = text.index("```", start)
    return text[start:end].strip()


def test_world_geography_rosters_cover_expected_country_sets():
    expected_rosters = {
        "02-africa-country-profiles.mdx": {
            "Algeria",
            "Angola",
            "Benin",
            "Botswana",
            "Burkina Faso",
            "Burundi",
            "Cameroon",
            "Cape Verde",
            "Central African Republic",
            "Chad",
            "Comoros",
            "DR Congo",
            "Djibouti",
            "Egypt",
            "Equatorial Guinea",
            "Eritrea",
            "Eswatini",
            "Ethiopia",
            "Gabon",
            "Gambia",
            "Ghana",
            "Guinea",
            "Guinea-Bissau",
            "Ivory Coast",
            "Kenya",
            "Lesotho",
            "Liberia",
            "Libya",
            "Madagascar",
            "Malawi",
            "Mali",
            "Mauritania",
            "Mauritius",
            "Morocco",
            "Mozambique",
            "Namibia",
            "Niger",
            "Nigeria",
            "Republic of the Congo",
            "Rwanda",
            "Senegal",
            "Seychelles",
            "Sierra Leone",
            "Somalia",
            "South Africa",
            "South Sudan",
            "Sudan",
            "Sao Tome and Principe",
            "Tanzania",
            "Togo",
            "Tunisia",
            "Uganda",
            "Zambia",
            "Zimbabwe",
        },
        "03-americas-country-profiles.mdx": {
            "Antigua and Barbuda",
            "Argentina",
            "Bahamas",
            "Barbados",
            "Belize",
            "Bolivia",
            "Brazil",
            "Canada",
            "Chile",
            "Colombia",
            "Costa Rica",
            "Cuba",
            "Dominica",
            "Dominican Republic",
            "Ecuador",
            "El Salvador",
            "Grenada",
            "Guatemala",
            "Guyana",
            "Haiti",
            "Honduras",
            "Jamaica",
            "Mexico",
            "Nicaragua",
            "Panama",
            "Paraguay",
            "Peru",
            "Saint Kitts and Nevis",
            "Saint Lucia",
            "Saint Vincent and the Grenadines",
            "Suriname",
            "Trinidad and Tobago",
            "United States",
            "Uruguay",
            "Venezuela",
        },
        "04-asia-country-profiles.mdx": {
            "Afghanistan",
            "Bangladesh",
            "Bhutan",
            "Brunei",
            "Cambodia",
            "China",
            "India",
            "Indonesia",
            "Japan",
            "Laos",
            "Malaysia",
            "Maldives",
            "Mongolia",
            "Myanmar",
            "Nepal",
            "North Korea",
            "Pakistan",
            "Philippines",
            "Singapore",
            "South Korea",
            "Sri Lanka",
            "Taiwan",
            "Thailand",
            "Timor-Leste",
            "Vietnam",
        },
        "05-europe-country-profiles.mdx": {
            "Albania",
            "Andorra",
            "Austria",
            "Belarus",
            "Belgium",
            "Bosnia and Herzegovina",
            "Bulgaria",
            "Croatia",
            "Cyprus",
            "Czechia",
            "Denmark",
            "Estonia",
            "Finland",
            "France",
            "Germany",
            "Greece",
            "Hungary",
            "Iceland",
            "Ireland",
            "Italy",
            "Kosovo",
            "Latvia",
            "Liechtenstein",
            "Lithuania",
            "Luxembourg",
            "Malta",
            "Moldova",
            "Monaco",
            "Montenegro",
            "Netherlands",
            "North Macedonia",
            "Norway",
            "Poland",
            "Portugal",
            "Romania",
            "Russia",
            "San Marino",
            "Serbia",
            "Slovakia",
            "Slovenia",
            "Spain",
            "Sweden",
            "Switzerland",
            "Ukraine",
            "United Kingdom",
            "Vatican City",
        },
        "06-middle-east-and-central-asia-country-profiles.mdx": {
            "Armenia",
            "Azerbaijan",
            "Bahrain",
            "Georgia",
            "Iran",
            "Iraq",
            "Israel",
            "Jordan",
            "Kazakhstan",
            "Kuwait",
            "Kyrgyzstan",
            "Lebanon",
            "Oman",
            "Palestine",
            "Qatar",
            "Saudi Arabia",
            "Syria",
            "Tajikistan",
            "Turkey",
            "Turkmenistan",
            "United Arab Emirates",
            "Uzbekistan",
            "Yemen",
        },
        "07-oceania-country-profiles.mdx": {
            "Australia",
            "Fiji",
            "Kiribati",
            "Marshall Islands",
            "Micronesia",
            "Nauru",
            "New Zealand",
            "Palau",
            "Papua New Guinea",
            "Samoa",
            "Solomon Islands",
            "Tonga",
            "Tuvalu",
            "Vanuatu",
        },
    }

    all_countries: set[str] = set()
    for filename, expected in expected_rosters.items():
        actual = _roster_countries(filename)
        assert actual == expected
        all_countries.update(actual)

    assert len(all_countries) == 197


def test_world_geography_region_chapters_include_map_blocks():
    expected_map_ids = {
        "02-africa-country-profiles.mdx": '"mapId": "africa"',
        "03-americas-country-profiles.mdx": '"mapId": "americas"',
        "04-asia-country-profiles.mdx": '"mapId": "asia"',
        "05-europe-country-profiles.mdx": '"mapId": "europe"',
        "06-middle-east-and-central-asia-country-profiles.mdx": '"mapId": "middle-east-central-asia"',
        "07-oceania-country-profiles.mdx": '"mapId": "oceania"',
    }

    for filename, expected_map_id in expected_map_ids.items():
        block = _map_block(filename)
        assert expected_map_id in block
        assert '"title":' in block
        assert '"note":' in block
