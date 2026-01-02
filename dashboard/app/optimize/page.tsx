'use client';

import { useState } from 'react';
import { useOptimizeSharpe, useRebalancing } from '@/hooks/useOptimize';
import { MetricCard } from '@/components/shared/MetricCard';
import { PeriodSelector } from '@/components/shared/PeriodSelector';
import { formatCurrency, formatPercent } from '@/lib/formatters';
import { Target, TrendingUp, ArrowUpDown, AlertCircle } from 'lucide-react';

export default function OptimizePage() {
  const [days, setDays] = useState(365);
  const { data: optimal, isLoading: isOptimalLoading } = useOptimizeSharpe(days, 5);
  const { data: rebalance, isLoading: isRebalanceLoading } = useRebalancing(days, 5);

  if (isOptimalLoading || isRebalanceLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading optimization...</div>
      </div>
    );
  }

  const hasOptimal = optimal?.success && optimal?.weights;
  const hasRebalancing = rebalance?.success && rebalance?.recommendations;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Portfolio Optimization</h1>
          <p className="mt-2 text-gray-600">
            Maximize risk-adjusted returns with optimal allocation
          </p>
        </div>
        <PeriodSelector selectedDays={days} onSelect={setDays} />
      </div>

      {/* Optimal Portfolio Metrics */}
      {hasOptimal && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Optimal Portfolio (Maximum Sharpe Ratio)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <MetricCard
              title="Expected Return"
              value={formatPercent(optimal.metrics.expected_return * 100)}
              subtitle="Annualized expected return"
              icon={TrendingUp}
            />
            <MetricCard
              title="Volatility"
              value={formatPercent(optimal.metrics.volatility * 100)}
              subtitle="Annualized standard deviation"
            />
            <MetricCard
              title="Sharpe Ratio"
              value={optimal.metrics.sharpe_ratio?.toFixed(2) || 'N/A'}
              subtitle="Risk-adjusted return metric"
              icon={Target}
            />
          </div>
        </div>
      )}

      {/* Optimal Allocation */}
      {hasOptimal && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Optimal Allocation
          </h3>
          <div className="space-y-3">
            {Object.entries(optimal.weights).map(([ticker, weight]: [string, any]) => (
              <div key={ticker} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-sm font-medium text-gray-900">{ticker}</div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-sm text-gray-600">
                    {formatPercent(weight * 100)}
                  </div>
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${weight * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rebalancing Recommendations */}
      {hasRebalancing && rebalance.recommendations.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <ArrowUpDown className="h-6 w-6 text-orange-600" />
            <h3 className="text-lg font-semibold text-gray-900">
              Rebalancing Recommendations
            </h3>
          </div>
          <div className="space-y-3">
            {rebalance.recommendations.map((rec: any, index: number) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <div
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      rec.action === 'BUY'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {rec.action}
                  </div>
                  <div className="text-sm font-medium text-gray-900">{rec.ticker}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {formatCurrency(Math.abs(rec.amount))}
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatPercent(Math.abs(rec.difference) * 100)} diff
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {(!hasOptimal || !hasRebalancing) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-center space-x-3">
            <AlertCircle className="h-5 w-5 text-yellow-800" />
            <div>
              <h3 className="text-sm font-semibold text-yellow-900">
                Insufficient Data
              </h3>
              <p className="text-sm text-yellow-800 mt-1">
                Need more historical data to calculate optimal portfolio. The system requires
                at least 30 days of price history for 5+ holdings.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Footer */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">
          About Portfolio Optimization
        </h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p>
            <strong>Sharpe Ratio Optimization:</strong> Finds the portfolio allocation that
            maximizes risk-adjusted returns (return per unit of risk).
          </p>
          <p>
            <strong>Rebalancing:</strong> Compares your current allocation with the optimal
            allocation and suggests trades to improve your portfolio's risk-return profile.
          </p>
          <p className="text-xs text-blue-700 mt-3">
            Note: These recommendations are based on historical data and do not guarantee future
            performance. Always consider your investment goals and risk tolerance.
          </p>
        </div>
      </div>
    </div>
  );
}
