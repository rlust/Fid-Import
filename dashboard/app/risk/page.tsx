'use client';

import { useState } from 'react';
import { useComprehensiveRisk } from '@/hooks/useRisk';
import { MetricCard } from '@/components/shared/MetricCard';
import { PeriodSelector } from '@/components/shared/PeriodSelector';
import { CorrelationHeatmap } from '@/components/visualizations/CorrelationHeatmap';
import { formatCurrency, formatPercent } from '@/lib/formatters';
import { AlertTriangle, TrendingDown, Shield, Target, Download } from 'lucide-react';

export default function RiskPage() {
  const [days, setDays] = useState(365);
  const { data: riskData, isLoading } = useComprehensiveRisk(days);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading risk analytics...</div>
      </div>
    );
  }

  const volatility = riskData?.volatility;
  const sharpe = riskData?.sharpe_ratio;
  const beta = riskData?.beta;
  const var_data = riskData?.value_at_risk;
  const drawdown = riskData?.max_drawdown;
  const correlation = riskData?.correlation_matrix;

  const exportToCSV = () => {
    if (!riskData) return;

    const csvSections: string[] = [];

    // Header
    csvSections.push('PORTFOLIO RISK ANALYTICS REPORT');
    csvSections.push(`Period: ${days} days`);
    csvSections.push(`Generated: ${new Date().toISOString()}`);
    csvSections.push('');

    // Volatility Metrics
    csvSections.push('VOLATILITY METRICS');
    csvSections.push('Metric,Value,Description');
    if (volatility) {
      csvSections.push(
        `Daily Volatility,${volatility.daily_volatility?.toFixed(4) || 'N/A'}%,Standard deviation of daily returns`
      );
      csvSections.push(
        `Annualized Volatility,${volatility.annualized_volatility?.toFixed(2) || 'N/A'}%,Volatility scaled to annual basis`
      );
      csvSections.push(
        `Data Points,${volatility.data_points || 0},Number of snapshots analyzed`
      );
    }
    csvSections.push('');

    // Risk-Adjusted Returns
    csvSections.push('RISK-ADJUSTED RETURNS');
    csvSections.push('Metric,Value,Description');
    if (sharpe) {
      csvSections.push(
        `Sharpe Ratio,${sharpe.sharpe_ratio?.toFixed(3) || 'N/A'},Return per unit of risk (higher is better)`
      );
      csvSections.push(
        `Annualized Return,${(sharpe.annualized_return * 100)?.toFixed(2) || 'N/A'}%,Average annual return`
      );
      csvSections.push(
        `Risk-Free Rate,${(sharpe.risk_free_rate * 100)?.toFixed(2) || 'N/A'}%,Benchmark for risk-free returns`
      );
    }
    csvSections.push('');

    // Market Risk
    csvSections.push('MARKET RISK (vs S&P 500)');
    csvSections.push('Metric,Value,Description');
    if (beta) {
      const betaInterpretation = beta.beta > 1
        ? 'More volatile than market'
        : beta.beta < 1
        ? 'Less volatile than market'
        : 'Aligned with market';
      csvSections.push(
        `Beta,${beta.beta?.toFixed(3) || 'N/A'},${betaInterpretation}`
      );
      csvSections.push(
        `Alpha,${beta.alpha?.toFixed(2) || 'N/A'}%,Excess return vs market`
      );
      csvSections.push(
        `R-Squared,${beta.r_squared?.toFixed(3) || 'N/A'},How well returns match market`
      );
      csvSections.push(
        `Correlation,${beta.correlation?.toFixed(3) || 'N/A'},Relationship with market`
      );
      csvSections.push(
        `Data Points,${beta.data_points || 0},Number of snapshots used`
      );
    }
    csvSections.push('');

    // Downside Risk
    csvSections.push('DOWNSIDE RISK');
    csvSections.push('Metric,Value,Description');
    if (var_data) {
      csvSections.push(
        `Value at Risk (95%),${formatCurrency(Math.abs(var_data.var_amount))},Potential loss at 95% confidence`
      );
      csvSections.push(
        `VaR Percentage,${Math.abs(var_data.var_percent)?.toFixed(2) || 'N/A'}%,VaR as % of portfolio`
      );
    }
    if (drawdown) {
      csvSections.push(
        `Maximum Drawdown,${Math.abs(drawdown.max_drawdown_percent)?.toFixed(2) || 'N/A'}%,Largest peak-to-trough decline`
      );
      csvSections.push(
        `Max Drawdown Amount,${formatCurrency(Math.abs(drawdown.max_drawdown_amount))},Dollar value of max drawdown`
      );
      if (drawdown.peak_date) {
        csvSections.push(`Peak Date,${new Date(drawdown.peak_date).toLocaleDateString()},Date of portfolio peak`);
        csvSections.push(`Trough Date,${new Date(drawdown.trough_date).toLocaleDateString()},Date of portfolio trough`);
        if (drawdown.recovery_date) {
          csvSections.push(`Recovery Date,${new Date(drawdown.recovery_date).toLocaleDateString()},Date of recovery to peak`);
        }
      }
    }
    csvSections.push('');

    // Risk Summary
    csvSections.push('RISK SUMMARY');
    let sharpeInterpretation = 'N/A';
    if (sharpe?.sharpe_ratio) {
      if (sharpe.sharpe_ratio > 2) sharpeInterpretation = 'Excellent';
      else if (sharpe.sharpe_ratio > 1) sharpeInterpretation = 'Good';
      else if (sharpe.sharpe_ratio > 0) sharpeInterpretation = 'Moderate';
      else sharpeInterpretation = 'Poor';
    }
    csvSections.push(`Sharpe Ratio Assessment,${sharpeInterpretation}`);

    if (beta?.beta) {
      const volatilityVsMarket = beta.beta > 1.2
        ? 'Significantly more volatile than market'
        : beta.beta > 1
        ? 'Moderately more volatile than market'
        : beta.beta > 0.8
        ? 'Similar volatility to market'
        : 'Less volatile than market';
      csvSections.push(`Market Volatility Comparison,${volatilityVsMarket}`);
    }

    const csvContent = csvSections.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `portfolio-risk-report-${days}d-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Risk Analytics</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Understand your portfolio's risk profile and volatility
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={exportToCSV}
            disabled={isLoading}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            title="Export risk report to CSV"
          >
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Export Report</span>
          </button>
          <PeriodSelector selectedDays={days} onSelect={setDays} />
        </div>
      </div>

      {/* Volatility Metrics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Volatility</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MetricCard
            title="Daily Volatility"
            value={
              volatility?.daily_volatility !== null
                ? formatPercent(volatility?.daily_volatility)
                : 'N/A'
            }
            subtitle="Standard deviation of daily returns"
            icon={TrendingDown}
          />
          <MetricCard
            title="Annualized Volatility"
            value={
              volatility?.annualized_volatility !== null
                ? formatPercent(volatility?.annualized_volatility)
                : 'N/A'
            }
            subtitle="Volatility scaled to annual basis"
            icon={TrendingDown}
          />
          <MetricCard
            title="Data Points"
            value={volatility?.data_points?.toString() || '0'}
            subtitle="Number of snapshots analyzed"
          />
        </div>
      </div>

      {/* Risk-Adjusted Returns */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Risk-Adjusted Returns
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MetricCard
            title="Sharpe Ratio"
            value={
              sharpe?.sharpe_ratio !== null
                ? sharpe?.sharpe_ratio?.toFixed(2)
                : 'N/A'
            }
            subtitle="Return per unit of risk (higher is better)"
            icon={Target}
          />
          <MetricCard
            title="Annualized Return"
            value={
              sharpe?.annualized_return !== null
                ? formatPercent(sharpe?.annualized_return * 100)
                : 'N/A'
            }
            subtitle="Average annual return"
          />
          <MetricCard
            title="Risk-Free Rate"
            value={formatPercent(sharpe?.risk_free_rate * 100)}
            subtitle="Benchmark for risk-free returns"
          />
        </div>
      </div>

      {/* Market Risk */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Market Risk (vs S&P 500)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <MetricCard
            title="Beta"
            value={beta?.beta !== null ? beta?.beta?.toFixed(2) : 'N/A'}
            subtitle={
              beta?.beta !== null && beta?.beta > 1
                ? 'More volatile than market'
                : beta?.beta !== null && beta?.beta < 1
                ? 'Less volatile than market'
                : 'Sensitivity to market movements'
            }
            icon={Shield}
          />
          <MetricCard
            title="Alpha"
            value={
              beta?.alpha !== null ? formatPercent(beta?.alpha) : 'N/A'
            }
            subtitle="Excess return vs market"
          />
          <MetricCard
            title="R-Squared"
            value={
              beta?.r_squared !== null ? beta?.r_squared?.toFixed(3) : 'N/A'
            }
            subtitle="How well returns match market"
          />
          <MetricCard
            title="Correlation"
            value={
              beta?.correlation !== null
                ? beta?.correlation?.toFixed(3)
                : 'N/A'
            }
            subtitle="Relationship with market"
          />
        </div>
        {beta?.data_points === 0 && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center space-x-2 text-yellow-800">
              <AlertTriangle className="h-5 w-5" />
              <span className="text-sm font-medium">
                No benchmark data available. Beta metrics require S&P 500 historical data.
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Downside Risk */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Downside Risk
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Value at Risk */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Value at Risk (95% confidence)
              </h3>
            </div>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Potential Loss</div>
                <div className="text-3xl font-bold text-red-600 dark:text-red-400">
                  {var_data?.var_amount !== null
                    ? formatCurrency(Math.abs(var_data?.var_amount))
                    : 'N/A'}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {var_data?.var_percent !== null
                    ? `${Math.abs(var_data?.var_percent).toFixed(2)}% of portfolio`
                    : ''}
                </div>
              </div>
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  There is a 5% chance of losing more than this amount in a single day
                  based on historical data.
                </div>
              </div>
            </div>
          </div>

          {/* Maximum Drawdown */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <TrendingDown className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Maximum Drawdown
              </h3>
            </div>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Largest Peak-to-Trough Decline</div>
                <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                  {drawdown?.max_drawdown_percent !== null
                    ? `${Math.abs(drawdown?.max_drawdown_percent).toFixed(2)}%`
                    : 'N/A'}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {drawdown?.max_drawdown_amount !== null
                    ? formatCurrency(Math.abs(drawdown?.max_drawdown_amount))
                    : ''}
                </div>
              </div>
              {drawdown?.peak_date && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  <div>Peak: {new Date(drawdown.peak_date).toLocaleDateString()}</div>
                  <div>Trough: {new Date(drawdown.trough_date).toLocaleDateString()}</div>
                  {drawdown.recovery_date && (
                    <div>Recovery: {new Date(drawdown.recovery_date).toLocaleDateString()}</div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Correlation Matrix */}
      {correlation && Object.keys(correlation).length > 0 && (
        <CorrelationHeatmap
          data={correlation}
          title="Holdings Correlation Matrix"
        />
      )}

      {/* Info Footer */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">
          Understanding Risk Metrics
        </h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p>
            <strong>Sharpe Ratio:</strong> Measures risk-adjusted returns. Values above 1 are good, above 2 are excellent.
          </p>
          <p>
            <strong>Beta:</strong> Measures volatility relative to the market. Beta &gt; 1 means more volatile, &lt; 1 means less volatile.
          </p>
          <p>
            <strong>VaR:</strong> Estimates the maximum potential loss at a given confidence level based on historical data.
          </p>
          <p>
            <strong>Max Drawdown:</strong> The largest peak-to-trough decline. Helps assess worst-case scenarios.
          </p>
        </div>
      </div>
    </div>
  );
}
