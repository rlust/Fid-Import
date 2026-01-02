/**
 * Formatting utilities for currency, percentages, and numbers
 */

export function formatCurrency(value: number | undefined | null): string {
  if (value === undefined || value === null) return 'N/A';

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number | undefined | null): string {
  if (value === undefined || value === null) return 'N/A';

  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value / 100);
}

export function formatNumber(value: number | undefined | null): string {
  if (value === undefined || value === null) return 'N/A';

  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatCompactNumber(value: number | undefined | null): string {
  if (value === undefined || value === null) return 'N/A';

  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    compactDisplay: 'short',
    maximumFractionDigits: 1,
  }).format(value);
}

export function formatDate(date: string | Date | undefined | null): string {
  if (!date) return 'N/A';

  try {
    let d: Date;

    if (typeof date === 'string') {
      // Handle old format: YYYYMMDD_HHMMSS
      if (date.match(/^\d{8}_\d{6}$/)) {
        const year = date.substring(0, 4);
        const month = date.substring(4, 6);
        const day = date.substring(6, 8);
        d = new Date(`${year}-${month}-${day}`);
      } else {
        d = new Date(date);
      }
    } else {
      d = date;
    }

    // Check if date is valid
    if (isNaN(d.getTime())) {
      return 'Invalid Date';
    }

    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(d);
  } catch (error) {
    return 'Invalid Date';
  }
}

export function formatDateTime(date: string | Date | undefined | null): string {
  if (!date) return 'N/A';

  try {
    let d: Date;

    if (typeof date === 'string') {
      // Handle old format: YYYYMMDD_HHMMSS
      if (date.match(/^\d{8}_\d{6}$/)) {
        const year = date.substring(0, 4);
        const month = date.substring(4, 6);
        const day = date.substring(6, 8);
        const hour = date.substring(9, 11);
        const minute = date.substring(11, 13);
        const second = date.substring(13, 15);
        d = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`);
      } else {
        d = new Date(date);
      }
    } else {
      d = date;
    }

    // Check if date is valid
    if (isNaN(d.getTime())) {
      return 'Invalid Date';
    }

    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(d);
  } catch (error) {
    return 'Invalid Date';
  }
}
