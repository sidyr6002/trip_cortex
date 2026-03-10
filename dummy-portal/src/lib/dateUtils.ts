/** "Mon, Jan 6" */
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  });
}

/** "06 Jan" */
export function formatDateShort(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short',
  });
}

/** "14:30" */
export function formatTime(dateStr: string): string {
  return dateStr.split('T')[1].substring(0, 5);
}

/** "Mon, 6 Jan 2025, 02:30 PM" */
export function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

/** "2025-01-06" */
export function toISODate(date: Date): string {
  return date.toISOString().split('T')[0];
}

/** "6 Jan 2025" */
export function formatDateLong(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
}

/** "02:30 PM" */
export function formatTimePM(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
}

/** "2h 30m" or "2h" */
export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}
