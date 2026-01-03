'use client';

import { usePortfolioSummary, useHoldings, usePortfolioHistory } from '@/hooks/usePortfolio';
import { useTransactions } from '@/hooks/useTransactions';
import { MetricCard } from '@/components/shared/MetricCard';
import { formatCurrency, formatDateTime } from '@/lib/formatters';
import { Database, TrendingUp, ArrowDownCircle, Calendar, CheckCircle2, Clock, RefreshCw, Activity } from 'lucide-react';
import { useMemo } from 'react';

export default function ImportStatusPage() {
  const { data: summary, isLoading: summaryLoading } = usePortfolioSummary();
  const { data: holdings, isLoading: holdingsLoading } = useHoldings();
  const { data: transactions, isLoading: transactionsLoading } = useTransactions({ limit: 1000 });
  const { data: history, isLoading: historyLoading } = usePortfolioHistory(365);

  // Calculate import statistics
  const importStats = useMemo(() => {
    if (!holdings || !transactions || !history) {
      return {
        totalHoldings: 0,
        totalTransactions: 0,
        totalSnapshots: 0,
        dateRange: { earliest: null, latest: null },
        uniqueAccounts: 0,
        uniqueTickers: 0,
      };
    }

    // Get unique tickers and accounts
    const tickers = new Set(holdings.map(h => h.symbol));
    const accounts = new Set(transactions.map((t: any) => t.account_id).filter(Boolean));

    // Find date range from transactions
    const dates = transactions
      .map((t: any) => new Date(t.transaction_date))
      .filter(d => !isNaN(d.getTime()));

    const earliest = dates.length > 0 ? new Date(Math.min(...dates.map(d => d.getTime()))) : null;
    const latest = dates.length > 0 ? new Date(Math.max(...dates.map(d => d.getTime()))) : null;

    return {
      totalHoldings: holdings.length,
      totalTransactions: transactions.length,
      totalSnapshots: history.history?.length || 0,
      dateRange: { earliest, latest },
      uniqueAccounts: accounts.size,
      uniqueTickers: tickers.size,
    };
  }, [holdings, transactions, history]);

  const isLoading = summaryLoading || holdingsLoading || transactionsLoading || historyLoading;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Data Import Status</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Comprehensive view of automatically imported portfolio data
        </p>
      </div>

      {/* Sync Status Banner */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
        <div className="flex items-center space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/50 rounded-full flex items-center justify-center">
              <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Auto-Import Active</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Data is automatically synchronized from Fidelity and updated in real-time
            </p>
          </div>
          <div className="flex-shrink-0">
            <div className="flex items-center space-x-2 text-sm text-green-700 dark:text-green-400">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span className="font-medium">Syncing</span>
            </div>
          </div>
        </div>
      </div>

      {/* Last Update Info */}
      {summary?.last_updated && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Clock className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Last Updated</p>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                  {formatDateTime(summary.last_updated)}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500 dark:text-gray-400">Portfolio Value</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {formatCurrency(summary.total_value)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Import Statistics Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Import Statistics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total Holdings"
            value={isLoading ? 'Loading...' : importStats.totalHoldings}
            subtitle={`${importStats.uniqueTickers} unique tickers`}
            icon={Database}
          />
          <MetricCard
            title="Total Transactions"
            value={isLoading ? 'Loading...' : importStats.totalTransactions}
            subtitle={`${importStats.uniqueAccounts} accounts`}
            icon={ArrowDownCircle}
          />
          <MetricCard
            title="Historical Snapshots"
            value={isLoading ? 'Loading...' : importStats.totalSnapshots}
            subtitle="Daily portfolio values"
            icon={Activity}
          />
          <MetricCard
            title="Data Coverage"
            value={
              importStats.dateRange.earliest && importStats.dateRange.latest
                ? `${Math.ceil((importStats.dateRange.latest.getTime() - importStats.dateRange.earliest.getTime()) / (1000 * 60 * 60 * 24))} days`
                : 'N/A'
            }
            subtitle="Transaction history"
            icon={Calendar}
          />
        </div>
      </div>

      {/* Data Timeline */}
      {importStats.dateRange.earliest && importStats.dateRange.latest && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center space-x-3 mb-6">
            <TrendingUp className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Data Timeline</h2>
          </div>

          <div className="space-y-6">
            {/* Timeline visualization */}
            <div className="relative">
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-600 via-blue-600 to-green-600"></div>

              {/* Earliest transaction */}
              <div className="relative flex items-start space-x-4 pb-6">
                <div className="flex-shrink-0 w-8 h-8 bg-purple-100 dark:bg-purple-900/50 rounded-full flex items-center justify-center border-2 border-purple-600 dark:border-purple-400">
                  <div className="w-3 h-3 bg-purple-600 dark:bg-purple-400 rounded-full"></div>
                </div>
                <div className="flex-1 bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">First Transaction</p>
                  <p className="text-lg font-semibold text-purple-600 dark:text-purple-400 mt-1">
                    {importStats.dateRange.earliest.toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Portfolio tracking began
                  </p>
                </div>
              </div>

              {/* Data collection period */}
              <div className="relative flex items-start space-x-4 pb-6">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/50 rounded-full flex items-center justify-center border-2 border-blue-600 dark:border-blue-400">
                  <div className="w-3 h-3 bg-blue-600 dark:bg-blue-400 rounded-full"></div>
                </div>
                <div className="flex-1 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">Data Collection Period</p>
                  <p className="text-lg font-semibold text-blue-600 dark:text-blue-400 mt-1">
                    {importStats.totalTransactions.toLocaleString()} Transactions
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Across {importStats.uniqueAccounts} account{importStats.uniqueAccounts !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>

              {/* Latest update */}
              <div className="relative flex items-start space-x-4">
                <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900/50 rounded-full flex items-center justify-center border-2 border-green-600 dark:border-green-400">
                  <div className="w-3 h-3 bg-green-600 dark:bg-green-400 rounded-full animate-pulse"></div>
                </div>
                <div className="flex-1 bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">Latest Transaction</p>
                  <p className="text-lg font-semibold text-green-600 dark:text-green-400 mt-1">
                    {importStats.dateRange.latest.toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Currently tracking {importStats.totalHoldings} position{importStats.totalHoldings !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Holdings Breakdown */}
      {holdings && holdings.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Current Holdings Breakdown
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Top sectors */}
            {Array.from(new Set(holdings.map(h => h.sector || 'Other')))
              .slice(0, 8)
              .map((sector, index) => {
                const sectorHoldings = holdings.filter(h => (h.sector || 'Other') === sector);
                const sectorValue = sectorHoldings.reduce((sum, h) => sum + (h.value || 0), 0);
                const percentage = summary?.total_value ? (sectorValue / summary.total_value) * 100 : 0;

                const colors = [
                  'from-blue-500 to-blue-600',
                  'from-purple-500 to-purple-600',
                  'from-green-500 to-green-600',
                  'from-yellow-500 to-yellow-600',
                  'from-red-500 to-red-600',
                  'from-indigo-500 to-indigo-600',
                  'from-pink-500 to-pink-600',
                  'from-teal-500 to-teal-600',
                ];

                return (
                  <div
                    key={sector}
                    className={`bg-gradient-to-br ${colors[index % colors.length]} rounded-lg p-4 text-white`}
                  >
                    <p className="text-xs font-medium opacity-90">{sector}</p>
                    <p className="text-2xl font-bold mt-2">{sectorHoldings.length}</p>
                    <p className="text-xs opacity-90 mt-1">{percentage.toFixed(1)}% of portfolio</p>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Import Success Message */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <Database className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          <div>
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300">
              Automated Data Import System
            </h3>
            <p className="text-sm text-blue-800 dark:text-blue-400 mt-1">
              Your portfolio data is automatically synchronized from Fidelity and stored securely.
              The system tracks {importStats.totalTransactions.toLocaleString()} historical transactions
              across {importStats.uniqueTickers} securities, providing comprehensive analytics and insights.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
