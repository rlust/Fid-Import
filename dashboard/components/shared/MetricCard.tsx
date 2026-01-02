import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: number;
  changeLabel?: string;
  icon?: LucideIcon;
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  change,
  changeLabel,
  icon: Icon,
  className,
}: MetricCardProps) {
  const isPositive = change !== undefined && change >= 0;

  return (
    <div className={cn('bg-white rounded-lg border border-gray-200 p-6', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{value}</p>
          {subtitle && (
            <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
          )}
          {change != null && (
            <div className="mt-2 flex items-center">
              <span
                className={cn(
                  'text-sm font-medium',
                  isPositive ? 'text-green-600' : 'text-red-600'
                )}
              >
                {isPositive ? '+' : ''}{change.toFixed(2)}%
              </span>
              {changeLabel && (
                <span className="ml-2 text-sm text-gray-500">{changeLabel}</span>
              )}
            </div>
          )}
        </div>
        {Icon && (
          <div className="ml-4">
            <div className="rounded-lg bg-blue-50 p-3">
              <Icon className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
