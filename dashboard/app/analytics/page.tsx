'use client';

import { useState } from 'react';
import { useComprehensiveRisk } from '@/hooks/useRisk';
import { usePerformance, useTopContributors, useSectorAttribution, usePerformanceHistory, useBenchmarkComparison } from '@/hooks/usePerformance';
import { useSectorAllocation } from '@/hooks/usePortfolio';
import { PeriodSelector } from '@/components/shared/PeriodSelector';
import { MetricCard } from '@/components/shared/MetricCard';
import { SectorPieChart } from '@/components/visualizations/SectorPieChart';
import { CorrelationHeatmap } from '@/components/visualizations/CorrelationHeatmap';
import { InteractivePerformanceChart } from '@/components/visualizations/InteractivePerformanceChart';
import { formatPercent, formatCurrency } from '@/lib/formatters';
import { TrendingUp, Target, Shield, AlertTriangle, PieChart as PieChartIcon, Download, BarChart3 } from 'lucide-react';

export default function AnalyticsPage() {
  const [days, setDays] = useState(365);
  const [showBenchmark, setShowBenchmark] = useState(true);

  const { data: riskData, isLoading: riskLoading } = useComprehensiveRisk(days);
  const { data: performance, isLoading: perfLoading } = usePerformance(days);
  const { data: contributors, isLoading: contribLoading } = useTopContributors(Math.min(days, 30));
  const { data: sectorAttribution, isLoading: sectorLoading } = useSectorAttribution(Math.min(days, 30));
  const { data: sectors, isLoading: sectorsLoading } = useSectorAllocation();
  const { data: performanceHistory, isLoading: historyLoading } = usePerformanceHistory(days);
  const { data: benchmarkComparison, isLoading: benchmarkLoading } = useBenchmarkComparison(days);

  // Transform sectors for pie chart
  const sectorPieData = sectors?.map((sector) => ({
    name: sector.sector,
    value: sector.value || 0,
    percentage: sector.percentage || 0,
  })) || [];

  // Transform performance history for chart with optional benchmark
  const chartData = benchmarkComparison?.history?.map((point: any) => ({
    date: point.timestamp,
    value: point.portfolio_value, // Normalized to 100
    benchmark: showBenchmark && point.benchmark_value ? point.benchmark_value : undefined,
    return: point.portfolio_return_percent,
  })) || performanceHistory?.history?.map((point: any) => ({
    date: point.timestamp,
    value: point.total_value,
    return: point.cumulative_return_percent,
  })) || [];

  const isLoading = riskLoading || perfLoading;

  const exportToCSV = () => {
    if (!performance && !riskData && !contributors && !sectorAttribution) return;

    const csvSections: string[] = [];

    // Key Metrics Section
    csvSections.push('KEY METRICS');
    csvSections.push('Metric,Value,Period');
    csvSections.push(
      `Time-Weighted Return,${performance?.returns?.twr_percent?.toFixed(2) || 'N/A'}%,${days} days`
    );
    csvSections.push(
      `Sharpe Ratio,${riskData?.sharpe_ratio?.sharpe_ratio?.toFixed(2) || 'N/A'},Risk-adjusted return`
    );
    csvSections.push(
      `Portfolio Beta,${riskData?.beta?.beta?.toFixed(2) || 'N/A'},vs S&P 500`
    );
    csvSections.push(
      `Annualized Volatility,${riskData?.volatility?.annualized_volatility?.toFixed(2) || 'N/A'}%,Annualized`
    );
    csvSections.push('');

    // Top Contributors Section
    if (contributors?.top_contributors && contributors.top_contributors.length > 0) {
      csvSections.push('TOP PERFORMANCE CONTRIBUTORS (Last 30 Days)');
      csvSections.push('Ticker,Portfolio Weight %,Holding Return %,Contribution %');
      contributors.top_contributors.slice(0, 10).forEach((holding: any) => {
        csvSections.push(
          `${holding.ticker},${holding.weight_percent?.toFixed(2) || 0},${
            holding.holding_return_percent?.toFixed(2) || 0
          },${holding.contribution_percent?.toFixed(2) || 0}`
        );
      });
      csvSections.push('');
    }

    // Sector Attribution Section
    if (sectorAttribution && sectorAttribution.length > 0) {
      csvSections.push('SECTOR ATTRIBUTION (Last 30 Days)');
      csvSections.push('Sector,Weight %,Holdings Count,Sector Return %,Contribution %');
      sectorAttribution.forEach((sector: any) => {
        csvSections.push(
          `${sector.sector || 'Unknown'},${sector.weight_percent?.toFixed(2) || 0},${
            sector.holdings_count || 0
          },${sector.sector_return_percent?.toFixed(2) || 0},${
            sector.contribution_percent?.toFixed(2) || 0
          }`
        );
      });
      csvSections.push('');
    }

    // Risk Metrics Section
    if (riskData) {
      csvSections.push('DETAILED RISK METRICS');
      csvSections.push('Metric,Value');
      if (riskData.volatility) {
        csvSections.push(`Daily Volatility,${riskData.volatility.daily_volatility?.toFixed(4) || 'N/A'}%`);
        csvSections.push(`Annualized Volatility,${riskData.volatility.annualized_volatility?.toFixed(2) || 'N/A'}%`);
      }
      if (riskData.sharpe_ratio) {
        csvSections.push(`Sharpe Ratio,${riskData.sharpe_ratio.sharpe_ratio?.toFixed(3) || 'N/A'}`);
        csvSections.push(`Annualized Return,${(riskData.sharpe_ratio.annualized_return * 100)?.toFixed(2) || 'N/A'}%`);
      }
      if (riskData.beta) {
        csvSections.push(`Beta,${riskData.beta.beta?.toFixed(3) || 'N/A'}`);
        csvSections.push(`Alpha,${riskData.beta.alpha?.toFixed(2) || 'N/A'}%`);
        csvSections.push(`R-Squared,${riskData.beta.r_squared?.toFixed(3) || 'N/A'}`);
      }
    }

    const csvContent = csvSections.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `portfolio-analytics-${days}d-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Advanced Analytics</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Comprehensive performance, risk, and allocation analytics
          </p>
        </div>
        <div className="flex items-center space-x-4 flex-shrink-0">
          <button
            onClick={exportToCSV}
            disabled={isLoading}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            title="Export analytics report to CSV"
          >
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Export Report</span>
          </button>
          <PeriodSelector selectedDays={days} onSelect={setDays} />
        </div>
      </div>

      {/* Key Metrics Overview */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Key Metrics</h2>
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Time-Weighted Return"
              value={formatPercent(performance?.returns?.twr_percent)}
              subtitle={`${days} day period`}
              icon={TrendingUp}
            />
            <MetricCard
              title="Sharpe Ratio"
              value={
                riskData?.sharpe_ratio?.sharpe_ratio !== null
                  ? riskData?.sharpe_ratio?.sharpe_ratio?.toFixed(2)
                  : 'N/A'
              }
              subtitle="Risk-adjusted return"
              icon={Target}
            />
            <MetricCard
              title="Portfolio Beta"
              value={
                riskData?.beta?.beta !== null
                  ? riskData?.beta?.beta?.toFixed(2)
                  : 'N/A'
              }
              subtitle="vs S&P 500"
              icon={Shield}
            />
            <MetricCard
              title="Volatility"
              value={
                riskData?.volatility?.annualized_volatility !== null
                  ? formatPercent(riskData?.volatility?.annualized_volatility)
                  : 'N/A'
              }
              subtitle="Annualized"
              icon={AlertTriangle}
            />
          </div>
        )}
      </div>

      {/* Benchmark Comparison Metrics */}
      {benchmarkComparison?.summary && benchmarkComparison.benchmark_available && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <BarChart3 className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Portfolio vs S&P 500
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Portfolio Return</div>
              <div className={`text-2xl font-bold ${benchmarkComparison.summary.portfolio_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {benchmarkComparison.summary.portfolio_return >= 0 ? '+' : ''}
                {formatPercent(benchmarkComparison.summary.portfolio_return)}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">S&P 500 Return</div>
              <div className={`text-2xl font-bold ${benchmarkComparison.summary.benchmark_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {benchmarkComparison.summary.benchmark_return >= 0 ? '+' : ''}
                {formatPercent(benchmarkComparison.summary.benchmark_return)}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                Alpha {benchmarkComparison.summary.outperforming ? '(Outperforming)' : '(Underperforming)'}
              </div>
              <div className={`text-2xl font-bold ${benchmarkComparison.summary.alpha >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {benchmarkComparison.summary.alpha >= 0 ? '+' : ''}
                {formatPercent(benchmarkComparison.summary.alpha)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Portfolio Performance History */}
      {!historyLoading && chartData.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Performance Chart ({days} days)
            </h3>
            {benchmarkComparison?.benchmark_available && (
              <button
                onClick={() => setShowBenchmark(!showBenchmark)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  showBenchmark
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                }`}
              >
                <BarChart3 className="h-4 w-4" />
                <span>{showBenchmark ? 'Hide' : 'Show'} S&P 500</span>
              </button>
            )}
          </div>
          <InteractivePerformanceChart
            data={chartData}
            title=""
            showBenchmark={showBenchmark && benchmarkComparison?.benchmark_available}
            showReturns={false}
            height={450}
          />
        </div>
      )}

      {/* Sector Allocation */}
      {!sectorsLoading && sectorPieData.length > 0 && (
        <SectorPieChart
          data={sectorPieData}
          title="Sector Allocation"
        />
      )}

      {/* Top Performance Contributors */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center space-x-3 mb-4">
          <TrendingUp className="h-6 w-6 text-green-600" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Top Performance Contributors (Last 30 Days)
          </h2>
        </div>
        {contribLoading ? (
          <div className="text-gray-500 dark:text-gray-400">Loading...</div>
        ) : contributors?.top_contributors && contributors.top_contributors.length > 0 ? (
          <div className="space-y-3">
            {contributors.top_contributors.slice(0, 5).map((holding: any) => (
              <div key={holding.ticker} className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-700 last:border-0">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <div className="font-semibold text-gray-900 dark:text-white">{holding.ticker}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {formatPercent(holding.weight_percent)} of portfolio
                    </div>
                  </div>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    Return: {formatPercent(holding.holding_return_percent)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-green-600">
                    +{formatPercent(holding.contribution_percent)}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">contribution</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500 dark:text-gray-400">No contributor data available</div>
        )}
      </div>

      {/* Sector Attribution */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center space-x-3 mb-4">
          <PieChartIcon className="h-6 w-6 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Sector Attribution (Last 30 Days)
          </h2>
        </div>
        {sectorLoading ? (
          <div className="text-gray-500 dark:text-gray-400">Loading...</div>
        ) : sectorAttribution && sectorAttribution.length > 0 ? (
          <div className="space-y-4">
            {sectorAttribution.map((sector: any) => (
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
                        (sector.contribution || 0) >= 0 ? 'text-green-600' : 'text-red-600'
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
                      (sector.contribution || 0) >= 0 ? 'bg-green-600' : 'bg-red-600'
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

      {/* Correlation Matrix */}
      {riskData?.correlation_matrix && Object.keys(riskData.correlation_matrix).length > 0 && (
        <CorrelationHeatmap
          data={riskData.correlation_matrix}
          title="Holdings Correlation Matrix"
        />
      )}

      {/* Risk Summary */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">
          Analytics Summary
        </h3>
        <div className="text-sm text-blue-800 dark:text-blue-400 space-y-2">
          <p>
            <strong>Performance:</strong> Your portfolio has a time-weighted return of{' '}
            {formatPercent(performance?.returns?.twr_percent)} over the last {days} days.
          </p>
          <p>
            <strong>Risk Profile:</strong> With a Sharpe ratio of{' '}
            {riskData?.sharpe_ratio?.sharpe_ratio?.toFixed(2) || 'N/A'}, your portfolio is generating{' '}
            {riskData?.sharpe_ratio?.sharpe_ratio > 1 ? 'good' : 'moderate'} risk-adjusted returns.
          </p>
          <p>
            <strong>Market Exposure:</strong> A beta of {riskData?.beta?.beta?.toFixed(2) || 'N/A'} indicates your
            portfolio is{' '}
            {riskData?.beta?.beta > 1
              ? 'more volatile than'
              : riskData?.beta?.beta < 1
              ? 'less volatile than'
              : 'aligned with'}{' '}
            the broader market.
          </p>
        </div>
      </div>
    </div>
  );
}
