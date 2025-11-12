/**
 * Portfolio Chart Component
 * Displays top holdings in a bar chart
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useTopHoldings } from '@/hooks/usePortfolio';
import { Skeleton } from '@/components/ui/skeleton';
import { BarChart3 } from 'lucide-react';

export function PortfolioChart() {
  const { data: topHoldings, isLoading, isError } = useTopHoldings(10);

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

  if (isError || !topHoldings) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive">Failed to load chart data</p>
        </CardContent>
      </Card>
    );
  }

  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  const maxValue = Math.max(...topHoldings.map(h => h.value));

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Top 10 Holdings</CardTitle>
          <BarChart3 className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {topHoldings.map((holding, index) => {
            const percentage = (holding.value / maxValue) * 100;

            return (
              <div key={holding.ticker} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground w-6">{index + 1}.</span>
                    <span className="font-semibold">{holding.ticker}</span>
                    <span className="text-muted-foreground truncate max-w-[150px]">
                      {holding.companyName}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-muted-foreground text-xs">
                      {holding.weight.toFixed(2)}%
                    </span>
                    <span className="font-medium">{formatCurrency(holding.value)}</span>
                  </div>
                </div>
                <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full bg-primary transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export default PortfolioChart;
