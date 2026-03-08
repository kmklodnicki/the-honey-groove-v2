/**
 * Displays a user's custom title label (e.g. "Founder") as a small badge.
 * Used next to usernames across the app.
 */
export function TitleBadge({ label }) {
  if (!label) return null;
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide bg-honey/20 text-honey-amber border border-honey/30"
      data-testid="title-badge"
    >
      {label}
    </span>
  );
}
