import type { CurriculumMapBlock } from "@/types/curriculum";

export type WorldGeographyMapId =
  | "africa"
  | "americas"
  | "asia"
  | "europe"
  | "middle-east-central-asia"
  | "oceania";

interface RegionViewport {
  center: [number, number];
  scale: number;
  title: string;
}

export interface WorldGeographyCountryData {
  id: string;
  name: string;
  topologyKey: string;
  capital: string;
  subregion: string;
  geographyType: string;
  compactProfile: string;
  keyFact: string;
  landmarks: string[];
  isAnchor: boolean;
}

export interface WorldGeographyRegionMapData {
  mapId: WorldGeographyMapId;
  title: string;
  center: [number, number];
  scale: number;
  countries: WorldGeographyCountryData[];
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
  keyFact?: string;
  landmarks?: string[];
}

const REGION_VIEWPORTS: Record<WorldGeographyMapId, RegionViewport> = {
  africa: {
    center: [18, 6],
    scale: 310,
    title: "Africa map",
  },
  americas: {
    center: [-72, 13],
    scale: 155,
    title: "Americas map",
  },
  asia: {
    center: [95, 27],
    scale: 220,
    title: "Asia map",
  },
  europe: {
    center: [18, 55],
    scale: 430,
    title: "Europe map",
  },
  "middle-east-central-asia": {
    center: [57, 35],
    scale: 420,
    title: "Middle East and Central Asia map",
  },
  oceania: {
    center: [162, -18],
    scale: 255,
    title: "Oceania map",
  },
};

const TOPOLOGY_NAME_ALIASES: Record<string, string> = {
  "antigua-and-barbuda": "antigua-and-barb",
  "bosnia-and-herzegovina": "bosnia-and-herz",
  "cape-verde": "cabo-verde",
  "central-african-republic": "central-african-rep",
  "dr-congo": "dem-rep-congo",
  "dominican-republic": "dominican-rep",
  eswatini: "eswatini",
  "equatorial-guinea": "eq-guinea",
  "ivory-coast": "cote-d-ivoire",
  "marshall-islands": "marshall-is",
  "north-macedonia": "macedonia",
  "republic-of-the-congo": "congo",
  "saint-kitts-and-nevis": "st-kitts-and-nevis",
  "saint-vincent-and-the-grenadines": "st-vin-and-gren",
  "sao-tome-and-principe": "sao-tome-and-principe",
  "solomon-islands": "solomon-is",
  "south-sudan": "s-sudan",
  "united-states": "united-states-of-america",
  "vatican-city": "vatican",
};

export function buildWorldGeographyRegionMapData(
  block: CurriculumMapBlock,
  chapterContent?: string,
): WorldGeographyRegionMapData | null {
  const mapId = normalizeMapId(block.mapId);
  if (!mapId || !chapterContent) return null;

  const viewport = REGION_VIEWPORTS[mapId];
  const roster = parseRosterCountries(chapterContent);
  const anchors = parseAnchorCountries(chapterContent);

  const countries = Array.from(roster.values()).map((country) => {
    const anchor = anchors.get(normalizeCountryKey(country.name));

    return {
      id: toCountryId(country.name),
      name: country.name,
      topologyKey: resolveTopologyKey(country.name),
      capital: country.capital,
      subregion: country.subregion,
      geographyType: country.geographyType,
      compactProfile: country.compactProfile,
      keyFact: anchor?.keyFact ?? country.compactProfile,
      landmarks: anchor?.landmarks ?? [],
      isAnchor: Boolean(anchor),
    } satisfies WorldGeographyCountryData;
  });

  const defaultCountryId =
    countries.find(
      (country) =>
        normalizeCountryKey(country.name) ===
        normalizeCountryKey(block.initialCountry ?? countries[0]?.name ?? ""),
    )?.id ?? countries[0]?.id;

  if (!defaultCountryId || countries.length === 0) return null;

  return {
    mapId,
    title: block.title ?? viewport.title,
    center: viewport.center,
    scale: viewport.scale,
    countries,
    defaultCountryId,
  };
}

export function normalizeCountryKey(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/\p{Diacritic}/gu, "")
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
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
  if (normalized in REGION_VIEWPORTS) {
    return normalized as WorldGeographyMapId;
  }
  return null;
}

function resolveTopologyKey(countryName: string): string {
  const normalized = normalizeCountryKey(countryName);
  return TOPOLOGY_NAME_ALIASES[normalized] ?? normalized;
}

function toCountryId(value: string): string {
  return normalizeCountryKey(value);
}
