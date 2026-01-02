'use client';

import { useState } from 'react';
import { useComprehensiveRisk } from '@/hooks/useRisk';
import { MetricCard } from '@/components/shared/MetricCard';
import { PeriodSelector } from '@/components/shared/PeriodSelector';
import { formatCurrency, formatPercent } from '@/lib/formatters';
import { AlertTriangle, TrendingDown, Shield, Target } from 'lucide-react';

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

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Risk Analytics</h1>
          <p className="mt-2 text-gray-600">
            Understand your portfolio's risk profile and volatility
          </p>
        </div>
        <PeriodSelector value={days} onChange={setDays} />
      </div>

      {/* Volatility Metrics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Volatility</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MetricCard
            title="Daily Volatility"
            value={
              volatility?.daily_volatility !== null
                ? formatPercent(volatility?.daily_volatility)
                : 'N/A'
            }
            description="Standard deviation of daily returns"
            icon={TrendingDown}
          />
          <MetricCard
            title="Annualized Volatility"
            value={
              volatility?.annualized_volatility !== null
                ? formatPercent(volatility?.annualized_volatility)
                : 'N/A'
            }
            description="Volatility scaled to annual basis"
            icon={TrendingDown}
          />
          <MetricCard
            title="Data Points"
            value={volatility?.data_points?.toString() || '0'}
            description="Number of snapshots analyzed"
          />
        </div>
      </div>

      {/* Risk-Adjusted Returns */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
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
            description="Return per unit of risk (higher is better)"
            icon={Target}
            trend={sharpe?.sharpe_ratio > 1 ? 'up' : undefined}
          />
          <MetricCard
            title="Annualized Return"
            value={
              sharpe?.annualized_return !== null
                ? formatPercent(sharpe?.annualized_return * 100)
                : 'N/A'
            }
            description="Average annual return"
          />
          <MetricCard
            title="Risk-Free Rate"
            value={formatPercent(sharpe?.risk_free_rate * 100)}
            description="Benchmark for risk-free returns"
          />
        </div>
      </div>

      {/* Market Risk */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Market Risk (vs S&P 500)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <MetricCard
            title="Beta"
            value={beta?.beta !== null ? beta?.beta?.toFixed(2) : 'N/A'}
            description="Sensitivity to market movements"
            icon={Shield}
            subtitle={
              beta?.beta !== null && beta?.beta > 1
                ? 'More volatile than market'
                : beta?.beta !== null && beta?.beta < 1
                ? 'Less volatile than market'
                : undefined
            }
          />
          <MetricCard
            title="Alpha"
            value={
              beta?.alpha !== null ? formatPercent(beta?.alpha) : 'N/A'
            }
            description="Excess return vs market"
            trend={beta?.alpha > 0 ? 'up' : beta?.alpha < 0 ? 'down' : undefined}
          />
          <MetricCard
            title="R-Squared"
            value={
              beta?.r_squared !== null ? beta?.r_squared?.toFixed(3) : 'N/A'
            }
            description="How well returns match market"
          />
          <MetricCard
            title="Correlation"
            value={
              beta?.correlation !== null
                ? beta?.correlation?.toFixed(3)
                : 'N/A'
            }
            description="Relationship with market"
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
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Downside Risk
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Value at Risk */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="h-6 w-6 text-red-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                Value at Risk (95% confidence)
              </h3>
            </div>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-500">Potential Loss</div>
                <div className="text-3xl font-bold text-red-600">
                  {var_data?.var_amount !== null
                    ? formatCurrency(Math.abs(var_data?.var_amount))
                    : 'N/A'}
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  {var_data?.var_percent !== null
                    ? `${Math.abs(var_data?.var_percent).toFixed(2)}% of portfolio`
                    : ''}
                </div>
              </div>
              <div className="pt-4 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  There is a 5% chance of losing more than this amount in a single day
                  based on historical data.
                </div>
              </div>
            </div>
          </div>

          {/* Maximum Drawdown */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <TrendingDown className="h-6 w-6 text-orange-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                Maximum Drawdown
              </h3>
            </div>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-500">Largest Peak-to-Trough Decline</div>
                <div className="text-3xl font-bold text-orange-600">
                  {drawdown?.max_drawdown_percent !== null
                    ? `${Math.abs(drawdown?.max_drawdown_percent).toFixed(2)}%`
                    : 'N/A'}
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  {drawdown?.max_drawdown_amount !== null
                    ? formatCurrency(Math.abs(drawdown?.max_drawdown_amount))
                    : ''}
                </div>
              </div>
              {drawdown?.peak_date && (
                <div className="pt-4 border-t border-gray-200 text-sm text-gray-600 space-y-1">
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
