'use client';

import { useState } from 'react';
import { usePerformance, useTopContributors, useSectorAttribution } from '@/hooks/usePerformance';
import { usePortfolioHistory } from '@/hooks/usePortfolio';
import { MetricCard } from '@/components/shared/MetricCard';
import { PeriodSelector } from '@/components/shared/PeriodSelector';
import { InteractivePerformanceChart } from '@/components/visualizations/InteractivePerformanceChart';
import { formatCurrency, formatPercent, formatDate } from '@/lib/formatters';
import { TrendingUp, TrendingDown, Target, BarChart3, PieChart } from 'lucide-react';

export default function PerformancePage() {
  const [selectedPeriod, setSelectedPeriod] = useState(365);

  const { data: performance, isLoading: perfLoading, error: perfError } = usePerformance(selectedPeriod);
  const { data: contributors, isLoading: contribLoading } = useTopContributors(Math.min(selectedPeriod, 30));
  const { data: sectorAttribution, isLoading: sectorLoading } = useSectorAttribution(Math.min(selectedPeriod, 30));
  const { data: history, isLoading: historyLoading } = usePortfolioHistory(selectedPeriod);

  // Transform history data for interactive chart
  const chartData = history?.history?.map((point: any) => ({
    date: point.date,
    value: point.total_value,
  })) || [];

  if (perfError) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-6">
        <h2 className="text-lg font-semibold text-red-900 mb-2">Error Loading Performance Data</h2>
        <p className="text-red-700">
          {perfError instanceof Error ? perfError.message : 'Failed to load performance metrics'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Performance Analytics</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Track returns, attribution, and benchmark comparison
          </p>
        </div>
        <div className="flex-shrink-0">
          <PeriodSelector selectedDays={selectedPeriod} onSelect={setSelectedPeriod} />
        </div>
      </div>

      {/* Performance Metrics */}
      {perfLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ) : performance?.error ? (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
          <p className="text-yellow-900 dark:text-yellow-300 font-medium">Insufficient Data</p>
          <p className="text-yellow-700 dark:text-yellow-400 text-sm mt-1">{performance.message}</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Simple Return"
              value={formatPercent(performance?.returns?.simple_return_percent)}
              subtitle={`${performance?.period?.days || 0} days`}
              icon={TrendingUp}
            />
            <MetricCard
              title="Time-Weighted Return"
              value={formatPercent(performance?.returns?.twr_percent)}
              subtitle="TWR (eliminates cash flows)"
              change={performance?.returns?.twr_percent}
              icon={Target}
            />
            <MetricCard
              title="Money-Weighted Return"
              value={formatPercent(performance?.returns?.mwr_percent)}
              subtitle={performance?.returns?.mwr_converged ? 'MWR (IRR)' : 'MWR (not converged)'}
              icon={BarChart3}
            />
            <MetricCard
              title="Annualized TWR"
              value={formatPercent(performance?.returns?.annualized_twr_percent)}
              subtitle="Projected annual return"
              icon={PieChart}
            />
          </div>

          {/* Period Summary */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Period Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Start Date</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {formatDate(performance?.period?.start_date)}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {formatCurrency(performance?.values?.start_value)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">End Date</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {formatDate(performance?.period?.end_date)}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {formatCurrency(performance?.values?.end_value)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Change</p>
                <p
                  className={`text-lg font-semibold ${
                    (performance?.values?.change || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {formatCurrency(performance?.values?.change)}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {formatPercent(performance?.values?.change_percent)}
                </p>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Interactive Performance Chart */}
      {!historyLoading && chartData.length > 0 && (
        <InteractivePerformanceChart
          data={chartData}
          title="Portfolio Value Over Time"
          height={450}
        />
      )}

      {/* Top Contributors */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Top Contributors (Last 30 Days)
        </h2>
        {contribLoading ? (
          <div className="text-gray-500 dark:text-gray-400">Loading...</div>
        ) : contributors?.top_contributors && contributors.top_contributors.length > 0 ? (
          <div className="space-y-3">
            {contributors.top_contributors.slice(0, 5).map((holding: any) => (
              <div key={holding.ticker} className="flex flex-col sm:flex-row sm:items-center sm:justify-between py-3 border-b border-gray-100 dark:border-gray-700 last:border-0 gap-2">
                <div className="flex-1">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-3">
                    <div className="font-semibold text-gray-900 dark:text-white">{holding.ticker}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {formatPercent(holding.weight_percent)} of portfolio
                    </div>
                  </div>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    Return: {formatPercent(holding.holding_return_percent)}
                  </div>
                </div>
                <div className="text-left sm:text-right">
                  <div className="font-semibold text-green-600 dark:text-green-400">
                    +{formatPercent(holding.contribution_percent)}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">contribution</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500 dark:text-gray-400">No attribution data available</div>
        )}
      </div>

      {/* Sector Attribution */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Sector Attribution (Last 30 Days)
        </h2>
        {sectorLoading ? (
          <div className="text-gray-500 dark:text-gray-400">Loading...</div>
        ) : sectorAttribution && sectorAttribution.length > 0 ? (
          <div className="space-y-4">
            {sectorAttribution.slice(0, 5).map((sector: any) => (
              <div key={sector.sector} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-gray-900 dark:text-white">{sector.sector || 'Unknown'}</span>
                      <span className="text-gray-600 dark:text-gray-400">{formatPercent(sector.weight_percent)}</span>
                    </div>
                    <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      {sector.holdings_count} holdings • Return: {formatPercent(sector.sector_return_percent)}
                    </div>
                  </div>
                  <div className="ml-6 text-right">
                    <span
                      className={`text-sm font-medium ${
                        (sector.contribution || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {(sector.contribution || 0) >= 0 ? '+' : ''}
                      {formatPercent(sector.contribution_percent)}
                    </span>
                  </div>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      (sector.contribution || 0) >= 0 ? 'bg-green-600 dark:bg-green-400' : 'bg-red-600 dark:bg-red-400'
                    }`}
                    style={{
                      width: `${Math.min(Math.abs(sector.contribution_percent || 0) * 10, 100)}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500 dark:text-gray-400">No sector attribution data available</div>
        )}
      </div>
    </div>
  );
}
