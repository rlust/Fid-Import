'use client';

import { cn } from '@/lib/utils';

interface PeriodOption {
  label: string;
  days: number;
}

interface PeriodSelectorProps {
  selectedDays: number;
  onSelect: (days: number) => void;
  options?: PeriodOption[];
}

const DEFAULT_OPTIONS: PeriodOption[] = [
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
  { label: 'YTD', days: -1 }, // -1 for year-to-date
  { label: 'All', days: 3650 }, // ~10 years
];

export function PeriodSelector({ selectedDays, onSelect, options = DEFAULT_OPTIONS }: PeriodSelectorProps) {
  return (
    <div className="inline-flex rounded-lg border border-gray-200 bg-white p-1">
      {options.map((option) => (
        <button
          key={option.label}
          onClick={() => onSelect(option.days)}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors',
            selectedDays === option.days
              ? 'bg-blue-600 text-white'
              : 'text-gray-700 hover:bg-gray-100'
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
