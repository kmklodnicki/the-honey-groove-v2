/**
 * Convert a 2-letter ISO country code to a flag emoji.
 * e.g. "US" → "🇺🇸", "GB" → "🇬🇧"
 */
export function countryFlag(code) {
  if (!code || code.length !== 2) return '';
  const offset = 127397;
  return String.fromCodePoint(...[...code.toUpperCase()].map(c => c.charCodeAt(0) + offset));
}
