'use client';

import { usePortfolioSummary, useTopHoldings, useSectorAllocation, usePortfolioHistory, useHoldings } from '@/hooks/usePortfolio';
import { MetricCard } from '@/components/shared/MetricCard';
import { PortfolioTimeline } from '@/components/performance/PortfolioTimeline';
import { PortfolioTreemap } from '@/components/visualizations/PortfolioTreemap';
import { SectorPieChart } from '@/components/visualizations/SectorPieChart';
import { formatCurrency, formatPercent, formatDateTime } from '@/lib/formatters';
import { Wallet, TrendingUp, TrendingDown, Activity } from 'lucide-react';

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading, error: summaryError } = usePortfolioSummary();
  const { data: topHoldings, isLoading: holdingsLoading } = useTopHoldings(5);
  const { data: allHoldings, isLoading: allHoldingsLoading } = useHoldings();
  const { data: sectors, isLoading: sectorsLoading } = useSectorAllocation();
  const { data: history, isLoading: historyLoading } = usePortfolioHistory(30);

  // Transform holdings for treemap visualization
  const treemapData = allHoldings?.map((holding) => ({
    name: holding.symbol || 'N/A',
    size: holding.value || 0,
    value: holding.portfolio_weight ? holding.portfolio_weight / 100 : 0,
    sector: holding.sector || 'Other',
  })) || [];

  // Transform sectors for pie chart
  const sectorPieData = sectors?.map((sector) => ({
    name: sector.sector,
    value: sector.total_value || 0,
    percentage: sector.percentage || 0,
  })) || [];

  if (summaryError) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-6">
        <h2 className="text-lg font-semibold text-red-900 mb-2">Error Loading Portfolio</h2>
        <p className="text-red-700">
          Failed to connect to the backend API. Make sure the FastAPI server is running at localhost:8000.
        </p>
        <pre className="mt-4 text-sm text-red-600 bg-red-100 p-3 rounded">
          {summaryError instanceof Error ? summaryError.message : 'Unknown error'}
        </pre>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Overview of your investment portfolio
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Portfolio Value"
          value={summaryLoading ? 'Loading...' : formatCurrency(summary?.total_value)}
          subtitle={summary?.last_updated ? `As of ${formatDateTime(summary.last_updated)}` : undefined}
          icon={Wallet}
        />
        <MetricCard
          title="Total Holdings"
          value={summaryLoading ? 'Loading...' : summary?.total_holdings || 0}
          subtitle="Positions"
          icon={Activity}
        />
        <MetricCard
          title="Total Gain/Loss"
          value={summaryLoading ? 'Loading...' : formatCurrency(summary?.total_gain_loss)}
          change={summary?.total_return_percent}
          changeLabel="return"
          icon={summary?.total_gain_loss && summary.total_gain_loss >= 0 ? TrendingUp : TrendingDown}
        />
        <MetricCard
          title="Total Return"
          value={summaryLoading ? 'Loading...' : formatPercent(summary?.total_return_percent)}
          subtitle="All time"
          icon={TrendingUp}
        />
      </div>

      {/* Portfolio Timeline Chart */}
      <PortfolioTimeline data={history} isLoading={historyLoading} />

      {/* Portfolio Allocation Treemap */}
      {!allHoldingsLoading && treemapData.length > 0 && (
        <PortfolioTreemap
          data={treemapData}
          title="Portfolio Allocation by Holdings"
        />
      )}

      {/* Top Holdings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Top Holdings</h2>
        {holdingsLoading ? (
          <div className="text-gray-500 dark:text-gray-400">Loading...</div>
        ) : topHoldings && topHoldings.length > 0 ? (
          <div className="space-y-3">
            {topHoldings.map((holding, index) => (
              <div
                key={`${holding.symbol}-${holding.value}-${index}`}
                className="flex flex-col sm:flex-row sm:items-center sm:justify-between py-3 border-b border-gray-100 dark:border-gray-700 last:border-0 gap-2"
              >
                <div className="flex-1">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-3">
                    <div className="font-semibold text-gray-900 dark:text-white">{holding.symbol}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{holding.company_name}</div>
                  </div>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {holding.quantity} shares @ {formatCurrency(holding.last_price)}
                  </div>
                </div>
                <div className="text-left sm:text-right">
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {formatCurrency(holding.value)}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {formatPercent(holding.portfolio_weight)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500 dark:text-gray-400">No holdings data available</div>
        )}
      </div>

      {/* Sector Allocation - Pie Chart */}
      {!sectorsLoading && sectorPieData.length > 0 && (
        <SectorPieChart
          data={sectorPieData}
          title="Sector Allocation"
        />
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <a
          href="/transactions"
          className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:border-blue-300 dark:hover:border-blue-600 transition-colors cursor-pointer"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Add Transaction
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            Record a new buy, sell, or dividend transaction
          </p>
        </a>
        <a
          href="/performance"
          className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:border-blue-300 dark:hover:border-blue-600 transition-colors cursor-pointer"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            View Performance
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            Analyze returns and compare with benchmarks
          </p>
        </a>
        <a
          href="/analytics"
          className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:border-blue-300 dark:hover:border-blue-600 transition-colors cursor-pointer"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Advanced Analytics
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            Explore risk metrics and correlations
          </p>
        </a>
      </div>
    </div>
  );
}
