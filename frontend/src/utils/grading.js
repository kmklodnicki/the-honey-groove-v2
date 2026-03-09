// Honey Groove Dual Grading System
// Standard vinyl grades with branded honey descriptors

export const GRADE_MAP = {
  NM: {
    code: 'NM',
    full: 'Near Mint',
    honey: "Queen's Choice",
    emoji: '\uD83D\uDC51\uD83C\uDF6F',
    tooltip: 'As close to perfect as a record gets. Surfaces are clean, playback should be flawless, and the sleeve has been well cared for. A collector-grade copy worthy of the Queen Bee.',
    color: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  },
  'VG+': {
    code: 'VG+',
    full: 'Very Good Plus',
    honey: 'The Sweet Spot',
    emoji: '\uD83C\uDF6F',
    tooltip: 'A beautiful spinner with only light signs of handling. You might notice faint sleeve marks or minimal surface wear, but playback remains strong and enjoyable. This is the sweet spot most collectors aim for.',
    color: 'bg-lime-100 text-lime-700 border-lime-200',
  },
  VG: {
    code: 'VG',
    full: 'Very Good',
    honey: 'Hive Classic',
    emoji: '\uD83D\uDC1D',
    tooltip: 'A well-loved record with visible signs of use. Expect some surface noise, especially between tracks or during quieter moments, but the music still plays strong.',
    color: 'bg-amber-100 text-amber-700 border-amber-200',
  },
  'G+': {
    code: 'G+',
    full: 'Good Plus / Good',
    honey: 'Well-Worn Honeycomb',
    emoji: '\uD83C\uDF6F\uD83D\uDC1D',
    tooltip: 'Significant wear from years of play. Surface marks and noticeable noise are expected, but the record still plays through.',
    color: 'bg-orange-100 text-orange-700 border-orange-200',
  },
  G: {
    code: 'G',
    full: 'Good Plus / Good',
    honey: 'Well-Worn Honeycomb',
    emoji: '\uD83C\uDF6F\uD83D\uDC1D',
    tooltip: 'Significant wear from years of play. Surface marks and noticeable noise are expected, but the record still plays through.',
    color: 'bg-orange-100 text-orange-700 border-orange-200',
  },
  F: {
    code: 'F',
    full: 'Fair / Poor',
    honey: 'Sticky Situation',
    emoji: '\uD83E\uDEE0\uD83C\uDF6F',
    tooltip: 'Heavy wear, scratches, and strong playback noise are likely. Best suited for completionists or collectors looking to rescue a relic from the hive.',
    color: 'bg-red-100 text-red-700 border-red-200',
  },
  P: {
    code: 'P',
    full: 'Fair / Poor',
    honey: 'Sticky Situation',
    emoji: '\uD83E\uDEE0\uD83C\uDF6F',
    tooltip: 'Heavy wear, scratches, and strong playback noise are likely. Best suited for completionists or collectors looking to rescue a relic from the hive.',
    color: 'bg-red-100 text-red-700 border-red-200',
  },
};

// Dropdown options for listing/trade forms (5 grouped tiers)
export const GRADE_OPTIONS = [
  { value: 'NM', label: "NM - Queen's Choice \uD83D\uDC51\uD83C\uDF6F" },
  { value: 'VG+', label: 'VG+ - The Sweet Spot \uD83C\uDF6F' },
  { value: 'VG', label: 'VG - Hive Classic \uD83D\uDC1D' },
  { value: 'G+', label: 'G+ / G - Well-Worn Honeycomb \uD83C\uDF6F\uD83D\uDC1D' },
  { value: 'F', label: 'F / P - Sticky Situation \uD83E\uDEE0\uD83C\uDF6F' },
];

// Map legacy long-form values to standard codes
const LEGACY_MAP = {
  'Mint': 'NM',
  'Near Mint': 'NM',
  'Very Good Plus': 'VG+',
  'Very Good': 'VG',
  'Good Plus': 'G+',
  'Good': 'G',
  'Fair': 'F',
  'Poor': 'P',
};

/** Normalize any condition value (legacy or new) to a standard code */
export function normalizeGrade(raw) {
  if (!raw) return null;
  const trimmed = raw.trim();
  // Already a standard code
  if (GRADE_MAP[trimmed]) return trimmed;
  // Legacy long-form
  if (LEGACY_MAP[trimmed]) return LEGACY_MAP[trimmed];
  return trimmed;
}

/** Get the grade info object for any condition value */
export function getGradeInfo(raw) {
  const code = normalizeGrade(raw);
  return code ? GRADE_MAP[code] || null : null;
}

/** Format a condition for display: "VG+ - The Sweet Spot" */
export function formatGradeDisplay(raw) {
  const info = getGradeInfo(raw);
  if (!info) return raw || '';
  return `${info.code} - ${info.honey} ${info.emoji}`;
}

/** Get just the standard code from any condition value */
export function gradeCode(raw) {
  return normalizeGrade(raw) || raw || '';
}

/** Get the color classes for a grade pill */
export function gradeColorClass(raw) {
  const info = getGradeInfo(raw);
  return info?.color || 'bg-stone-100 text-stone-600 border-stone-200';
}
