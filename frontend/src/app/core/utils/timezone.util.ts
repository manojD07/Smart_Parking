/**
 * Timezone utilities for consistent IST handling in the frontend
 */

// Indian Standard Time timezone
export const IST_TIMEZONE = 'Asia/Kolkata';
export const IST_OFFSET = '+05:30';

/**
 * Get current date/time in IST
 */
export function nowIST(): Date {
  return new Date(new Date().toLocaleString("en-US", { timeZone: IST_TIMEZONE }));
}

/**
 * Convert any date to IST
 */
export function toIST(date: Date | string): Date {
  if (typeof date === 'string') {
    date = new Date(date);
  }
  return new Date(date.toLocaleString("en-US", { timeZone: IST_TIMEZONE }));
}

/**
 * Format date in IST with specific format
 */
export function formatIST(date: Date | string, options?: Intl.DateTimeFormatOptions): string {
  if (typeof date === 'string') {
    date = new Date(date);
  }
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    timeZone: IST_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  };
  
  return date.toLocaleString('en-IN', { ...defaultOptions, ...options });
}

/**
 * Format date for datetime-local input in IST
 */
export function toDatetimeLocalIST(date: Date | string): string {
  if (typeof date === 'string') {
    date = new Date(date);
  }
  
  // Convert to IST and format for datetime-local input
  const istDate = toIST(date);
  const year = istDate.getFullYear();
  const month = String(istDate.getMonth() + 1).padStart(2, '0');
  const day = String(istDate.getDate()).padStart(2, '0');
  const hours = String(istDate.getHours()).padStart(2, '0');
  const minutes = String(istDate.getMinutes()).padStart(2, '0');
  
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Convert datetime-local input value to ISO string in IST
 */
export function fromDatetimeLocalIST(value: string): string {
  if (!value) return '';
  
  // Create date object assuming the input is in IST
  const localDate = new Date(value);
  
  // Convert to IST and then to ISO string
  const istDate = toIST(localDate);
  return istDate.toISOString();
}

/**
 * Get relative time string (e.g., "2 hours ago", "in 30 minutes")
 */
export function getRelativeTimeIST(date: Date | string): string {
  if (typeof date === 'string') {
    date = new Date(date);
  }
  
  const now = nowIST();
  const diff = date.getTime() - now.getTime();
  const absDiff = Math.abs(diff);
  
  const seconds = Math.floor(absDiff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) {
    return diff > 0 ? `in ${days} day${days > 1 ? 's' : ''}` : `${days} day${days > 1 ? 's' : ''} ago`;
  } else if (hours > 0) {
    return diff > 0 ? `in ${hours} hour${hours > 1 ? 's' : ''}` : `${hours} hour${hours > 1 ? 's' : ''} ago`;
  } else if (minutes > 0) {
    return diff > 0 ? `in ${minutes} minute${minutes > 1 ? 's' : ''}` : `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  } else {
    return 'just now';
  }
}

/**
 * Check if a date is today in IST
 */
export function isTodayIST(date: Date | string): boolean {
  if (typeof date === 'string') {
    date = new Date(date);
  }
  
  const today = nowIST();
  const checkDate = toIST(date);
  
  return today.toDateString() === checkDate.toDateString();
}

/**
 * Get start of day in IST
 */
export function startOfDayIST(date?: Date): Date {
  const targetDate = date ? toIST(date) : nowIST();
  targetDate.setHours(0, 0, 0, 0);
  return targetDate;
}

/**
 * Get end of day in IST
 */
export function endOfDayIST(date?: Date): Date {
  const targetDate = date ? toIST(date) : nowIST();
  targetDate.setHours(23, 59, 59, 999);
  return targetDate;
}

/**
 * Parse backend ISO string to IST date
 */
export function parseBackendDate(isoString: string): Date {
  return toIST(new Date(isoString));
}

/**
 * Convert frontend date to backend format (ISO string)
 */
export function toBackendDate(date: Date): string {
  return toIST(date).toISOString();
}
