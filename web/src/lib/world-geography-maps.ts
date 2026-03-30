import type { CurriculumMapBlock } from "@/types/curriculum";

export type WorldGeographyMapId =
  | "africa"
  | "americas"
  | "asia"
  | "europe"
  | "middle-east-central-asia"
  | "oceania";

interface CountryMarkerLayout {
  name: string;
  x: number;
  y: number;
}

interface RegionLandmarkPin {
  id: string;
  country: string;
  x: number;
  y: number;
  fallbackLabel: string;
}

interface RegionLayout {
  mapId: WorldGeographyMapId;
  title: string;
  width: number;
  height: number;
  defaultCountry: string;
  backgroundPaths: string[];
  countries: CountryMarkerLayout[];
  landmarks: RegionLandmarkPin[];
}

export interface WorldGeographyCountryPoint {
  id: string;
  name: string;
  capital: string;
  subregion: string;
  geographyType: string;
  compactProfile: string;
  keyFact: string;
  landmarks: string[];
  isAnchor: boolean;
  x: number;
  y: number;
}

export interface WorldGeographyLandmarkPoint {
  id: string;
  label: string;
  countryId: string;
  countryName: string;
  x: number;
  y: number;
}

export interface WorldGeographyRegionMapData {
  mapId: WorldGeographyMapId;
  title: string;
  width: number;
  height: number;
  backgroundPaths: string[];
  countries: WorldGeographyCountryPoint[];
  landmarks: WorldGeographyLandmarkPoint[];
  defaultCountryId: string;
}

interface ParsedRosterCountry {
  name: string;
  capital: string;
  subregion: string;
  geographyType: string;
  compactProfile: string;
}

interface ParsedAnchorCountry {
  name: string;
  keyFact?: string;
  landmarks?: string[];
}

const WORLD_GEOGRAPHY_LAYOUTS: Record<WorldGeographyMapId, RegionLayout> = {
  africa: {
    mapId: "africa",
    title: "Africa map",
    width: 100,
    height: 100,
    defaultCountry: "Egypt",
    backgroundPaths: [
      "M19 9 L33 7 L49 9 L60 16 L68 29 L71 43 L74 59 L73 73 L68 89 L60 98 L48 94 L36 88 L28 79 L22 66 L17 52 L13 36 L14 22 L18 12 Z",
      "M72 73 L79 78 L81 89 L77 96 L71 91 L69 82 Z",
    ],
    countries: [
      { name: "Morocco", x: 14, y: 22 },
      { name: "Algeria", x: 22, y: 24 },
      { name: "Tunisia", x: 31, y: 24 },
      { name: "Libya", x: 40, y: 26 },
      { name: "Egypt", x: 50, y: 26 },
      { name: "Sudan", x: 48, y: 37 },
      { name: "South Sudan", x: 48, y: 49 },
      { name: "Eritrea", x: 56, y: 40 },
      { name: "Djibouti", x: 58, y: 44 },
      { name: "Ethiopia", x: 54, y: 47 },
      { name: "Somalia", x: 61, y: 52 },
      { name: "Mauritania", x: 14, y: 37 },
      { name: "Mali", x: 20, y: 42 },
      { name: "Senegal", x: 10, y: 45 },
      { name: "Gambia", x: 11, y: 47 },
      { name: "Guinea-Bissau", x: 12, y: 49 },
      { name: "Guinea", x: 15, y: 52 },
      { name: "Sierra Leone", x: 13, y: 55 },
      { name: "Liberia", x: 15, y: 58 },
      { name: "Ivory Coast", x: 20, y: 57 },
      { name: "Ghana", x: 24, y: 57 },
      { name: "Togo", x: 26, y: 57 },
      { name: "Benin", x: 28, y: 56 },
      { name: "Burkina Faso", x: 23, y: 49 },
      { name: "Niger", x: 30, y: 45 },
      { name: "Nigeria", x: 30, y: 55 },
      { name: "Cape Verde", x: 4, y: 46 },
      { name: "Chad", x: 38, y: 45 },
      { name: "Cameroon", x: 31, y: 58 },
      { name: "Central African Republic", x: 37, y: 54 },
      { name: "DR Congo", x: 40, y: 65 },
      { name: "Republic of the Congo", x: 37, y: 66 },
      { name: "Gabon", x: 31, y: 67 },
      { name: "Equatorial Guinea", x: 29, y: 64 },
      { name: "Sao Tome and Principe", x: 26, y: 71 },
      { name: "Angola", x: 34, y: 79 },
      { name: "Uganda", x: 48, y: 58 },
      { name: "Kenya", x: 53, y: 61 },
      { name: "Rwanda", x: 46, y: 63 },
      { name: "Burundi", x: 47, y: 66 },
      { name: "Tanzania", x: 51, y: 69 },
      { name: "Seychelles", x: 67, y: 63 },
      { name: "Comoros", x: 59, y: 73 },
      { name: "Madagascar", x: 65, y: 81 },
      { name: "Mauritius", x: 70, y: 84 },
      { name: "Malawi", x: 51, y: 76 },
      { name: "Zambia", x: 45, y: 77 },
      { name: "Zimbabwe", x: 49, y: 83 },
      { name: "Mozambique", x: 56, y: 83 },
      { name: "Namibia", x: 30, y: 84 },
      { name: "Botswana", x: 37, y: 86 },
      { name: "South Africa", x: 40, y: 94 },
      { name: "Lesotho", x: 43, y: 94 },
      { name: "Eswatini", x: 47, y: 89 },
    ],
    landmarks: [
      { id: "giza", country: "Egypt", x: 51, y: 24, fallbackLabel: "Giza" },
      { id: "lagos", country: "Nigeria", x: 27, y: 57, fallbackLabel: "Lagos" },
      { id: "lalibela", country: "Ethiopia", x: 53, y: 44, fallbackLabel: "Lalibela" },
      { id: "maasai", country: "Kenya", x: 54, y: 63, fallbackLabel: "Maasai Mara" },
      { id: "table-mountain", country: "South Africa", x: 38, y: 96, fallbackLabel: "Table Mountain" },
    ],
  },
  americas: {
    mapId: "americas",
    title: "Americas map",
    width: 100,
    height: 100,
    defaultCountry: "United States",
    backgroundPaths: [
      "M8 10 L18 6 L28 10 L33 19 L32 30 L28 42 L23 51 L20 61 L22 67 L18 74 L11 70 L9 59 L10 45 L8 31 L7 19 Z",
      "M31 63 L40 60 L49 63 L56 71 L58 81 L55 92 L48 99 L40 96 L35 87 L33 76 Z",
      "M31 42 L40 43 L48 47 L49 58 L43 64 L36 61 L31 52 Z",
    ],
    countries: [
      { name: "Canada", x: 20, y: 17 },
      { name: "United States", x: 22, y: 31 },
      { name: "Mexico", x: 20, y: 44 },
      { name: "Belize", x: 23, y: 51 },
      { name: "Guatemala", x: 21, y: 52 },
      { name: "Honduras", x: 25, y: 54 },
      { name: "El Salvador", x: 23, y: 56 },
      { name: "Nicaragua", x: 27, y: 58 },
      { name: "Costa Rica", x: 29, y: 61 },
      { name: "Panama", x: 32, y: 63 },
      { name: "Bahamas", x: 33, y: 39 },
      { name: "Cuba", x: 35, y: 44 },
      { name: "Jamaica", x: 40, y: 49 },
      { name: "Haiti", x: 43, y: 49 },
      { name: "Dominican Republic", x: 46, y: 49 },
      { name: "Antigua and Barbuda", x: 49, y: 53 },
      { name: "Saint Kitts and Nevis", x: 48, y: 52 },
      { name: "Dominica", x: 50, y: 56 },
      { name: "Saint Lucia", x: 51, y: 58 },
      { name: "Saint Vincent and the Grenadines", x: 50, y: 60 },
      { name: "Barbados", x: 54, y: 60 },
      { name: "Grenada", x: 49, y: 62 },
      { name: "Trinidad and Tobago", x: 49, y: 66 },
      { name: "Colombia", x: 37, y: 67 },
      { name: "Venezuela", x: 44, y: 68 },
      { name: "Guyana", x: 48, y: 73 },
      { name: "Suriname", x: 52, y: 74 },
      { name: "Ecuador", x: 36, y: 76 },
      { name: "Peru", x: 40, y: 82 },
      { name: "Brazil", x: 51, y: 82 },
      { name: "Bolivia", x: 45, y: 86 },
      { name: "Paraguay", x: 49, y: 91 },
      { name: "Chile", x: 34, y: 90 },
      { name: "Argentina", x: 43, y: 96 },
      { name: "Uruguay", x: 49, y: 97 },
    ],
    landmarks: [
      { id: "nyc", country: "United States", x: 27, y: 29, fallbackLabel: "Statue of Liberty" },
      { id: "niagara", country: "Canada", x: 25, y: 24, fallbackLabel: "Niagara Falls" },
      { id: "teotihuacan", country: "Mexico", x: 21, y: 42, fallbackLabel: "Teotihuacan" },
      { id: "christ", country: "Brazil", x: 54, y: 84, fallbackLabel: "Christ the Redeemer" },
      { id: "iguazu", country: "Argentina", x: 47, y: 91, fallbackLabel: "Iguazu Falls" },
    ],
  },
  asia: {
    mapId: "asia",
    title: "Asia map",
    width: 100,
    height: 100,
    defaultCountry: "China",
    backgroundPaths: [
      "M8 27 L19 16 L31 12 L46 10 L58 13 L69 18 L80 24 L89 34 L93 45 L89 55 L80 61 L72 66 L66 75 L56 82 L44 81 L34 74 L28 64 L20 61 L15 52 L10 42 Z",
      "M63 64 L70 67 L75 73 L73 81 L66 85 L61 79 L60 71 Z",
      "M83 55 L91 57 L95 63 L93 70 L86 68 L82 61 Z",
    ],
    countries: [
      { name: "Afghanistan", x: 26, y: 38 },
      { name: "Pakistan", x: 31, y: 45 },
      { name: "India", x: 37, y: 54 },
      { name: "Nepal", x: 40, y: 43 },
      { name: "Bhutan", x: 45, y: 44 },
      { name: "Bangladesh", x: 45, y: 49 },
      { name: "Sri Lanka", x: 40, y: 66 },
      { name: "Maldives", x: 31, y: 68 },
      { name: "China", x: 54, y: 33 },
      { name: "Mongolia", x: 56, y: 21 },
      { name: "North Korea", x: 75, y: 32 },
      { name: "South Korea", x: 77, y: 37 },
      { name: "Japan", x: 87, y: 36 },
      { name: "Taiwan", x: 76, y: 47 },
      { name: "Myanmar", x: 50, y: 52 },
      { name: "Thailand", x: 56, y: 58 },
      { name: "Laos", x: 59, y: 53 },
      { name: "Cambodia", x: 61, y: 59 },
      { name: "Vietnam", x: 64, y: 55 },
      { name: "Malaysia", x: 61, y: 69 },
      { name: "Singapore", x: 62, y: 76 },
      { name: "Brunei", x: 69, y: 68 },
      { name: "Indonesia", x: 72, y: 78 },
      { name: "Philippines", x: 80, y: 60 },
      { name: "Timor-Leste", x: 76, y: 85 },
    ],
    landmarks: [
      { id: "great-wall", country: "China", x: 56, y: 29, fallbackLabel: "Great Wall" },
      { id: "taj-mahal", country: "India", x: 39, y: 52, fallbackLabel: "Taj Mahal" },
      { id: "fuji", country: "Japan", x: 89, y: 38, fallbackLabel: "Mount Fuji" },
      { id: "borobudur", country: "Indonesia", x: 70, y: 80, fallbackLabel: "Borobudur" },
      { id: "marina-bay", country: "Singapore", x: 63, y: 77, fallbackLabel: "Marina Bay Sands" },
    ],
  },
  europe: {
    mapId: "europe",
    title: "Europe map",
    width: 100,
    height: 100,
    defaultCountry: "France",
    backgroundPaths: [
      "M10 18 L20 12 L33 13 L41 18 L51 17 L61 20 L71 26 L80 31 L84 42 L79 52 L70 55 L64 63 L55 67 L44 64 L37 58 L26 56 L18 49 L13 39 Z",
      "M43 66 L49 69 L52 77 L49 87 L42 81 L40 72 Z",
      "M69 69 L74 71 L76 77 L71 80 L66 76 Z",
    ],
    countries: [
      { name: "Iceland", x: 6, y: 11 },
      { name: "Ireland", x: 11, y: 28 },
      { name: "United Kingdom", x: 16, y: 25 },
      { name: "Portugal", x: 20, y: 59 },
      { name: "Spain", x: 25, y: 57 },
      { name: "Andorra", x: 27, y: 54 },
      { name: "France", x: 32, y: 47 },
      { name: "Belgium", x: 38, y: 39 },
      { name: "Netherlands", x: 39, y: 35 },
      { name: "Luxembourg", x: 38, y: 42 },
      { name: "Monaco", x: 36, y: 52 },
      { name: "Germany", x: 43, y: 40 },
      { name: "Denmark", x: 44, y: 28 },
      { name: "Norway", x: 38, y: 14 },
      { name: "Sweden", x: 48, y: 15 },
      { name: "Finland", x: 58, y: 16 },
      { name: "Estonia", x: 60, y: 19 },
      { name: "Latvia", x: 60, y: 24 },
      { name: "Lithuania", x: 59, y: 29 },
      { name: "Poland", x: 55, y: 38 },
      { name: "Czechia", x: 46, y: 37 },
      { name: "Slovakia", x: 51, y: 43 },
      { name: "Austria", x: 46, y: 44 },
      { name: "Switzerland", x: 40, y: 46 },
      { name: "Liechtenstein", x: 42, y: 48 },
      { name: "Italy", x: 45, y: 57 },
      { name: "San Marino", x: 46, y: 56 },
      { name: "Vatican City", x: 44, y: 59 },
      { name: "Slovenia", x: 44, y: 50 },
      { name: "Croatia", x: 48, y: 52 },
      { name: "Bosnia and Herzegovina", x: 50, y: 53 },
      { name: "Serbia", x: 54, y: 53 },
      { name: "Montenegro", x: 52, y: 57 },
      { name: "Kosovo", x: 55, y: 56 },
      { name: "Albania", x: 51, y: 60 },
      { name: "North Macedonia", x: 55, y: 58 },
      { name: "Greece", x: 58, y: 63 },
      { name: "Bulgaria", x: 60, y: 53 },
      { name: "Romania", x: 61, y: 47 },
      { name: "Moldova", x: 66, y: 44 },
      { name: "Ukraine", x: 71, y: 39 },
      { name: "Belarus", x: 65, y: 32 },
      { name: "Russia", x: 83, y: 22 },
      { name: "Hungary", x: 52, y: 47 },
      { name: "Cyprus", x: 69, y: 72 },
      { name: "Malta", x: 43, y: 71 },
    ],
    landmarks: [
      { id: "big-ben", country: "United Kingdom", x: 17, y: 23, fallbackLabel: "Big Ben" },
      { id: "eiffel", country: "France", x: 31, y: 46, fallbackLabel: "Eiffel Tower" },
      { id: "brandenburg", country: "Germany", x: 44, y: 39, fallbackLabel: "Brandenburg Gate" },
      { id: "colosseum", country: "Italy", x: 46, y: 58, fallbackLabel: "Colosseum" },
      { id: "sagrada", country: "Spain", x: 24, y: 55, fallbackLabel: "Sagrada Familia" },
      { id: "wawel", country: "Poland", x: 56, y: 40, fallbackLabel: "Wawel Castle" },
    ],
  },
  "middle-east-central-asia": {
    mapId: "middle-east-central-asia",
    title: "Middle East and Central Asia map",
    width: 100,
    height: 100,
    defaultCountry: "Turkey",
    backgroundPaths: [
      "M11 34 L20 24 L34 20 L48 19 L62 22 L75 28 L84 35 L89 45 L86 57 L77 63 L69 68 L58 73 L46 75 L34 71 L24 62 L18 54 L12 44 Z",
    ],
    countries: [
      { name: "Turkey", x: 22, y: 33 },
      { name: "Georgia", x: 33, y: 26 },
      { name: "Armenia", x: 36, y: 31 },
      { name: "Azerbaijan", x: 42, y: 31 },
      { name: "Syria", x: 28, y: 40 },
      { name: "Lebanon", x: 30, y: 42 },
      { name: "Israel", x: 31, y: 46 },
      { name: "Palestine", x: 32, y: 48 },
      { name: "Jordan", x: 35, y: 46 },
      { name: "Iraq", x: 41, y: 42 },
      { name: "Kuwait", x: 48, y: 49 },
      { name: "Saudi Arabia", x: 45, y: 59 },
      { name: "Bahrain", x: 53, y: 52 },
      { name: "Qatar", x: 55, y: 53 },
      { name: "United Arab Emirates", x: 59, y: 55 },
      { name: "Oman", x: 63, y: 60 },
      { name: "Yemen", x: 52, y: 68 },
      { name: "Iran", x: 53, y: 40 },
      { name: "Kazakhstan", x: 63, y: 23 },
      { name: "Uzbekistan", x: 66, y: 34 },
      { name: "Turkmenistan", x: 60, y: 37 },
      { name: "Kyrgyzstan", x: 73, y: 35 },
      { name: "Tajikistan", x: 72, y: 40 },
    ],
    landmarks: [
      { id: "hagia-sophia", country: "Turkey", x: 20, y: 31, fallbackLabel: "Hagia Sophia" },
      { id: "mecca", country: "Saudi Arabia", x: 43, y: 62, fallbackLabel: "Mecca" },
      { id: "persepolis", country: "Iran", x: 56, y: 45, fallbackLabel: "Persepolis" },
      { id: "western-wall", country: "Israel", x: 30, y: 45, fallbackLabel: "Western Wall" },
      { id: "bayterek", country: "Kazakhstan", x: 66, y: 21, fallbackLabel: "Bayterek Tower" },
    ],
  },
  oceania: {
    mapId: "oceania",
    title: "Oceania map",
    width: 100,
    height: 100,
    defaultCountry: "Australia",
    backgroundPaths: [
      "M19 56 L28 50 L42 50 L50 58 L48 69 L38 74 L24 72 L18 64 Z",
      "M53 78 L58 74 L62 78 L60 89 L55 93 L52 86 Z",
      "M61 46 L68 43 L73 48 L71 56 L64 58 L60 51 Z",
    ],
    countries: [
      { name: "Australia", x: 33, y: 62 },
      { name: "New Zealand", x: 57, y: 84 },
      { name: "Papua New Guinea", x: 56, y: 48 },
      { name: "Solomon Islands", x: 66, y: 53 },
      { name: "Vanuatu", x: 70, y: 60 },
      { name: "Fiji", x: 76, y: 61 },
      { name: "Samoa", x: 82, y: 57 },
      { name: "Tonga", x: 83, y: 67 },
      { name: "Tuvalu", x: 73, y: 49 },
      { name: "Kiribati", x: 79, y: 44 },
      { name: "Marshall Islands", x: 89, y: 38 },
      { name: "Micronesia", x: 83, y: 35 },
      { name: "Palau", x: 74, y: 36 },
      { name: "Nauru", x: 79, y: 51 },
    ],
    landmarks: [
      { id: "opera-house", country: "Australia", x: 40, y: 65, fallbackLabel: "Sydney Opera House" },
      { id: "milford", country: "New Zealand", x: 56, y: 87, fallbackLabel: "Milford Sound" },
      { id: "kokoda", country: "Papua New Guinea", x: 59, y: 49, fallbackLabel: "Kokoda Track" },
      { id: "mamanuca", country: "Fiji", x: 77, y: 60, fallbackLabel: "Mamanuca Islands" },
    ],
  },
};

export function buildWorldGeographyRegionMapData(
  block: CurriculumMapBlock,
  chapterContent?: string,
): WorldGeographyRegionMapData | null {
  const mapId = normalizeMapId(block.mapId);
  if (!mapId || !chapterContent) return null;

  const layout = WORLD_GEOGRAPHY_LAYOUTS[mapId];
  const roster = parseRosterCountries(chapterContent);
  const anchors = parseAnchorCountries(chapterContent);

  const countries = layout.countries
    .map((marker) => {
      const rosterCountry = roster.get(normalizeCountryKey(marker.name));
      if (!rosterCountry) return null;
      const anchorCountry = anchors.get(normalizeCountryKey(marker.name));
      const landmarks = anchorCountry?.landmarks ?? [];

      return {
        id: toCountryId(rosterCountry.name),
        name: rosterCountry.name,
        capital: rosterCountry.capital,
        subregion: rosterCountry.subregion,
        geographyType: rosterCountry.geographyType,
        compactProfile: rosterCountry.compactProfile,
        keyFact: anchorCountry?.keyFact ?? rosterCountry.compactProfile,
        landmarks,
        isAnchor: Boolean(anchorCountry),
        x: marker.x,
        y: marker.y,
      } satisfies WorldGeographyCountryPoint;
    })
    .filter((country): country is WorldGeographyCountryPoint => country !== null);

  const landmarks = layout.landmarks
    .map((pin) => {
      const country = countries.find(
        (candidate) => normalizeCountryKey(candidate.name) === normalizeCountryKey(pin.country),
      );
      if (!country) return null;
      return {
        id: pin.id,
        label: country.landmarks[0] ?? pin.fallbackLabel,
        countryId: country.id,
        countryName: country.name,
        x: pin.x,
        y: pin.y,
      } satisfies WorldGeographyLandmarkPoint;
    })
    .filter((pin): pin is WorldGeographyLandmarkPoint => pin !== null);

  const defaultCountryId =
    countries.find(
      (country) =>
        normalizeCountryKey(country.name) === normalizeCountryKey(block.initialCountry ?? layout.defaultCountry),
    )?.id ?? countries[0]?.id;

  if (!defaultCountryId || countries.length === 0) return null;

  return {
    mapId,
    title: block.title ?? layout.title,
    width: layout.width,
    height: layout.height,
    backgroundPaths: layout.backgroundPaths,
    countries,
    landmarks,
    defaultCountryId,
  };
}

function parseRosterCountries(content: string): Map<string, ParsedRosterCountry> {
  const rosterSection = sliceBetween(content, "## Complete regional roster", "## Summary");
  const countries = new Map<string, ParsedRosterCountry>();

  for (const line of rosterSection.split("\n")) {
    if (!line.startsWith("| ") || line.startsWith("| Country |") || line.startsWith("| ---")) {
      continue;
    }
    const cells = line
      .split("|")
      .map((cell) => cell.trim())
      .filter(Boolean);
    if (cells.length < 5) continue;
    const [name, capital, subregion, geographyType, compactProfile] = cells;
    countries.set(normalizeCountryKey(name), {
      name,
      capital,
      subregion,
      geographyType,
      compactProfile,
    });
  }

  return countries;
}

function parseAnchorCountries(content: string): Map<string, ParsedAnchorCountry> {
  const matches = Array.from(content.matchAll(/^##\s+(.+)\r?\n([\s\S]*?)(?=^##\s+|\Z)/gm));
  const ignoredSections = new Set([
    "Regional overview",
    "Subregions to know",
    "Comparing the five",
    "Comparing the six",
    "Comparing the four",
    "Complete regional roster",
    "Summary",
  ]);
  const anchors = new Map<string, ParsedAnchorCountry>();

  for (const match of matches) {
    const name = match[1]?.trim();
    const sectionBody = match[2] ?? "";
    if (!name || ignoredSections.has(name)) continue;

    const keyFact = matchBulletField(sectionBody, "Key facts");
    const famousLandmarks = matchBulletField(sectionBody, "Famous landmarks");
    const landmarks = famousLandmarks
      ? famousLandmarks
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean)
      : undefined;

    anchors.set(normalizeCountryKey(name), {
      name,
      keyFact: keyFact ?? undefined,
      landmarks,
    });
  }

  return anchors;
}

function matchBulletField(sectionBody: string, label: string): string | null {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = sectionBody.match(new RegExp(`^- \\*\\*${escaped}\\*\\*: (.+)$`, "m"));
  return match?.[1]?.trim() ?? null;
}

function sliceBetween(content: string, startMarker: string, endMarker: string): string {
  const startIndex = content.indexOf(startMarker);
  if (startIndex === -1) return "";
  const afterStart = content.slice(startIndex + startMarker.length);
  const endIndex = afterStart.indexOf(endMarker);
  return endIndex === -1 ? afterStart : afterStart.slice(0, endIndex);
}

function normalizeMapId(value: string): WorldGeographyMapId | null {
  const normalized = value.trim().toLowerCase();
  if (normalized in WORLD_GEOGRAPHY_LAYOUTS) {
    return normalized as WorldGeographyMapId;
  }
  return null;
}

function normalizeCountryKey(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/\p{Diacritic}/gu, "")
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
}

function toCountryId(value: string): string {
  return normalizeCountryKey(value);
}
