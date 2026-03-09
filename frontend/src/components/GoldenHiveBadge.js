/**
 * Displays the Golden Hive verified badge next to usernames.
 * Only shown for users with golden_hive === true.
 */
export function GoldenHiveBadge({ verified }) {
  if (!verified) return null;
  return (
    <span
      className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-700 border border-amber-300"
      data-testid="golden-hive-badge"
      title="Golden Hive Verified"
    >
      <svg className="w-2.5 h-2.5" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0l2.1 5.3L16 6.2l-4 3.8 1 5.7L8 13l-5 2.7 1-5.7-4-3.8 5.9-.9z"/></svg>
      Golden
    </span>
  );
}
