'use client';

import { useHoldings } from '@/hooks/usePortfolio';
import { MetricCard } from '@/components/shared/MetricCard';
import { PortfolioTreemap } from '@/components/visualizations/PortfolioTreemap';
import { formatCurrency, formatPercent, formatDateTime } from '@/lib/formatters';
import { TrendingUp, TrendingDown, Package } from 'lucide-react';

export default function HoldingsPage() {
  const { data: holdings, isLoading, error } = useHoldings();

  // Transform holdings for treemap visualization
  const treemapData = holdings?.map((holding) => ({
    name: holding.symbol || 'N/A',
    size: holding.value || 0,
    value: holding.portfolio_weight ? holding.portfolio_weight / 100 : 0,
    sector: holding.sector || 'Other',
  })) || [];

  // Calculate summary metrics
  const totalValue = holdings?.reduce((sum, h) => sum + (h.value || 0), 0) || 0;
  const totalGainLoss = holdings?.reduce((sum, h) => sum + (h.unrealized_gain_loss || 0), 0) || 0;
  const totalReturn = totalValue > 0 ? (totalGainLoss / (totalValue - totalGainLoss)) * 100 : 0;

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-6">
        <h2 className="text-lg font-semibold text-red-900 dark:text-red-300 mb-2">Error Loading Holdings</h2>
        <p className="text-red-700 dark:text-red-400">
          {error instanceof Error ? error.message : 'Failed to load holdings data'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Holdings</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Complete view of your portfolio positions
        </p>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard
          title="Total Holdings Value"
          value={isLoading ? 'Loading...' : formatCurrency(totalValue)}
          subtitle={`${holdings?.length || 0} positions`}
          icon={Package}
        />
        <MetricCard
          title="Total Gain/Loss"
          value={isLoading ? 'Loading...' : formatCurrency(totalGainLoss)}
          change={totalReturn}
          icon={totalGainLoss >= 0 ? TrendingUp : TrendingDown}
        />
        <MetricCard
          title="Average Return"
          value={isLoading ? 'Loading...' : formatPercent(totalReturn)}
          subtitle="Weighted by position size"
          icon={TrendingUp}
        />
      </div>

      {/* Portfolio Allocation Treemap */}
      {!isLoading && treemapData.length > 0 && (
        <PortfolioTreemap
          data={treemapData}
          title="Portfolio Allocation"
        />
      )}

      {/* Holdings Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">All Holdings</h2>
        {isLoading ? (
          <div className="text-gray-500 dark:text-gray-400">Loading holdings...</div>
        ) : holdings && holdings.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Symbol</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Name</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Quantity</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Price</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Value</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Weight</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Gain/Loss</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Sector</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {holdings.map((holding, index) => (
                  <tr key={`${holding.symbol}-${index}`} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="py-3 px-4 font-semibold text-gray-900 dark:text-white">
                      {holding.symbol}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {holding.company_name || '-'}
                    </td>
                    <td className="py-3 px-4 text-right text-sm text-gray-900 dark:text-white">
                      {holding.quantity?.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right text-sm text-gray-900 dark:text-white">
                      {formatCurrency(holding.last_price)}
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-gray-900 dark:text-white">
                      {formatCurrency(holding.value)}
                    </td>
                    <td className="py-3 px-4 text-right text-sm text-gray-600 dark:text-gray-400">
                      {formatPercent(holding.portfolio_weight)}
                    </td>
                    <td className={`py-3 px-4 text-right text-sm font-medium ${
                      (holding.unrealized_gain_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(holding.unrealized_gain_loss)}
                      <div className="text-xs">
                        {formatPercent(holding.unrealized_gain_loss_percent)}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {holding.sector || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No holdings data available. Add transactions to see your holdings.
          </div>
        )}
      </div>

      {/* Last Updated */}
      {holdings && holdings.length > 0 && holdings[0].last_updated && (
        <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
          Last updated: {formatDateTime(holdings[0].last_updated)}
        </div>
      )}
    </div>
  );
}
