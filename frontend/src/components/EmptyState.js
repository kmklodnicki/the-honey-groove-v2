/**
 * Shared reusable components extracted from ProfilePage.
 */
import { Card } from './ui/card';

export const EmptyState = ({ icon: Icon, title, sub, subStyle }) => (
  <Card className="p-8 text-center border-honey/30" data-testid="empty-state">
    <Icon className="w-12 h-12 text-honey mx-auto mb-4" />
    <h3 className="font-heading text-xl mb-2">{title}</h3>
    <p className="text-muted-foreground text-sm" style={subStyle}>{sub}</p>
  </Card>
);
