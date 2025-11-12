/**
 * Portfolio Summary Component
 * Displays key portfolio metrics in card format
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, DollarSign, Briefcase, Calendar } from 'lucide-react';
import { usePortfolioSummary, useHistoricalComparison } from '@/hooks/usePortfolio';
import { Skeleton } from '@/components/ui/skeleton';

export function PortfolioSummary() {
  const { data: summary, isLoading, isError } = usePortfolioSummary();
  const { data: comparison } = useHistoricalComparison();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map(i => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (isError || !summary) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive">Failed to load portfolio summary</p>
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Total Value Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Portfolio Value</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatCurrency(summary.totalValue)}</div>
          {comparison && (
            <div className="flex items-center mt-2">
              {comparison.percentChange >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
              )}
              <span
                className={`text-sm ${
                  comparison.percentChange >= 0 ? 'text-green-500' : 'text-red-500'
                }`}
              >
                {comparison.percentChange >= 0 ? '+' : ''}
                {comparison.percentChange.toFixed(2)}% (
                {formatCurrency(comparison.valueChange)})
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Total Holdings Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Holdings</CardTitle>
          <Briefcase className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{summary.totalHoldings}</div>
          {comparison && comparison.holdingsChange !== 0 && (
            <p className="text-xs text-muted-foreground mt-2">
              {comparison.holdingsChange > 0 ? '+' : ''}
              {comparison.holdingsChange} position
              {Math.abs(comparison.holdingsChange) !== 1 ? 's' : ''} from last update
            </p>
          )}
        </CardContent>
      </Card>

      {/* Last Updated Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
          <Calendar className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-lg font-semibold">{formatDate(summary.timestamp)}</div>
          <p className="text-xs text-muted-foreground mt-2">Snapshot #{summary.snapshotId}</p>
        </CardContent>
      </Card>
    </div>
  );
}

export default PortfolioSummary;
