/**
 * Sector Allocation Component
 * Displays portfolio allocation by sector in a pie chart
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useSectorAllocation } from '@/hooks/usePortfolio';
import { Skeleton } from '@/components/ui/skeleton';
import { PieChart } from 'lucide-react';

// Color palette for sectors
const SECTOR_COLORS: Record<string, string> = {
  Technology: 'bg-blue-500',
  'Financial Services': 'bg-green-500',
  Healthcare: 'bg-red-500',
  'Consumer Cyclical': 'bg-purple-500',
  'Consumer Defensive': 'bg-yellow-500',
  'Real Estate': 'bg-pink-500',
  Energy: 'bg-orange-500',
  'Basic Materials': 'bg-teal-500',
  Industrials: 'bg-indigo-500',
  Utilities: 'bg-cyan-500',
  'Communication Services': 'bg-violet-500',
  Cash: 'bg-gray-400',
  Other: 'bg-gray-300',
};

export function SectorAllocation() {
  const { data: sectors, isLoading, isError } = useSectorAllocation();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[400px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (isError || !sectors) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive">Failed to load sector data</p>
        </CardContent>
      </Card>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const totalValue = sectors.reduce((sum, s) => sum + s.value, 0);

  // Calculate cumulative percentages for the pie chart visualization
  let cumulativePercentage = 0;
  const sectorsWithAngles = sectors.map(sector => {
    const startAngle = cumulativePercentage;
    cumulativePercentage += sector.percentage;
    const endAngle = cumulativePercentage;

    return {
      ...sector,
      startAngle: (startAngle * 360) / 100,
      endAngle: (endAngle * 360) / 100,
    };
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Sector Allocation</CardTitle>
          <PieChart className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Visual Representation - Simple stacked bars */}
          <div className="space-y-2">
            <div className="flex h-8 w-full overflow-hidden rounded-lg">
              {sectors.map(sector => {
                const color = SECTOR_COLORS[sector.sector] || 'bg-gray-300';
                return (
                  <div
                    key={sector.sector}
                    className={`${color} transition-all duration-300 hover:opacity-80`}
                    style={{ width: `${sector.percentage}%` }}
                    title={`${sector.sector}: ${sector.percentage.toFixed(1)}%`}
                  />
                );
              })}
            </div>
          </div>

          {/* Legend with details */}
          <div className="space-y-3 pt-2">
            {sectors.map(sector => {
              const color = SECTOR_COLORS[sector.sector] || 'bg-gray-300';

              return (
                <div key={sector.sector} className="flex items-center justify-between">
                  <div className="flex items-center gap-2 flex-1">
                    <div className={`h-3 w-3 rounded-sm ${color}`} />
                    <span className="text-sm font-medium">{sector.sector}</span>
                    <span className="text-xs text-muted-foreground">
                      ({sector.holdings} position{sector.holdings !== 1 ? 's' : ''})
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-muted-foreground">
                      {sector.percentage.toFixed(1)}%
                    </span>
                    <span className="text-sm font-medium min-w-[100px] text-right">
                      {formatCurrency(sector.value)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Total */}
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">Total</span>
              <span className="text-sm font-semibold">{formatCurrency(totalValue)}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default SectorAllocation;
