'use client';

import { useState, useMemo } from 'react';
import { useHoldings } from '@/hooks/usePortfolio';
import { MetricCard } from '@/components/shared/MetricCard';
import { PortfolioTreemap } from '@/components/visualizations/PortfolioTreemap';
import { formatCurrency, formatPercent, formatDateTime } from '@/lib/formatters';
import { TrendingUp, TrendingDown, Package, Search, ArrowUpDown, Download } from 'lucide-react';

type SortField = 'symbol' | 'value' | 'weight' | 'gainLoss' | 'quantity';
type SortDirection = 'asc' | 'desc';

export default function HoldingsPage() {
  const { data: holdings, isLoading, error } = useHoldings();
  const [searchTerm, setSearchTerm] = useState('');
  const [sectorFilter, setSectorFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('value');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Get unique sectors for filter
  const sectors = useMemo(() => {
    if (!holdings) return [];
    const uniqueSectors = [...new Set(holdings.map(h => h.sector || 'Other'))];
    return uniqueSectors.sort();
  }, [holdings]);

  // Filter and sort holdings
  const filteredHoldings = useMemo(() => {
    if (!holdings) return [];

    let filtered = holdings.filter(holding => {
      const matchesSearch = holding.symbol?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          holding.company_name?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesSector = sectorFilter === 'all' || holding.sector === sectorFilter;
      return matchesSearch && matchesSector;
    });

    // Sort
    filtered.sort((a, b) => {
      let aVal, bVal;

      switch (sortField) {
        case 'symbol':
          aVal = a.symbol || '';
          bVal = b.symbol || '';
          break;
        case 'value':
          aVal = a.value || 0;
          bVal = b.value || 0;
          break;
        case 'weight':
          aVal = a.portfolio_weight || 0;
          bVal = b.portfolio_weight || 0;
          break;
        case 'gainLoss':
          aVal = a.unrealized_gain_loss || 0;
          bVal = b.unrealized_gain_loss || 0;
          break;
        case 'quantity':
          aVal = a.quantity || 0;
          bVal = b.quantity || 0;
          break;
        default:
          return 0;
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return filtered;
  }, [holdings, searchTerm, sectorFilter, sortField, sortDirection]);

  // Transform holdings for treemap visualization
  const treemapData = filteredHoldings?.map((holding) => ({
    name: holding.symbol || 'N/A',
    size: holding.value || 0,
    value: holding.portfolio_weight ? holding.portfolio_weight / 100 : 0,
    sector: holding.sector || 'Other',
  })) || [];

  // Calculate summary metrics
  const totalValue = filteredHoldings?.reduce((sum, h) => sum + (h.value || 0), 0) || 0;
  const totalGainLoss = filteredHoldings?.reduce((sum, h) => sum + (h.unrealized_gain_loss || 0), 0) || 0;
  const totalReturn = totalValue > 0 ? (totalGainLoss / (totalValue - totalGainLoss)) * 100 : 0;

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const exportToCSV = () => {
    if (!filteredHoldings || filteredHoldings.length === 0) return;

    const headers = ['Symbol', 'Name', 'Quantity', 'Price', 'Value', 'Weight %', 'Gain/Loss', 'Gain/Loss %', 'Sector'];
    const rows = filteredHoldings.map(h => [
      h.symbol,
      h.company_name || '',
      h.quantity,
      h.last_price,
      h.value,
      h.portfolio_weight,
      h.unrealized_gain_loss,
      h.unrealized_gain_loss_percent,
      h.sector || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `holdings-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Holdings</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Complete view of your portfolio positions
          </p>
        </div>
        {!isLoading && holdings && holdings.length > 0 && (
          <div className="flex-shrink-0">
            <button
              onClick={exportToCSV}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              title="Export holdings to CSV"
            >
              <Download className="h-4 w-4" />
              <span className="hidden sm:inline">Export CSV</span>
            </button>
          </div>
        )}
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard
          title="Total Holdings Value"
          value={isLoading ? 'Loading...' : formatCurrency(totalValue)}
          subtitle={`${filteredHoldings?.length || 0} positions`}
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

      {/* Search and Filters */}
      {!isLoading && holdings && holdings.length > 0 && (
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by symbol or name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Sector Filter */}
          <div className="sm:w-48">
            <select
              value={sectorFilter}
              onChange={(e) => setSectorFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Sectors</option>
              {sectors.map(sector => (
                <option key={sector} value={sector}>{sector}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Holdings Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">All Holdings</h2>
        {isLoading ? (
          <div className="text-gray-500 dark:text-gray-400">Loading holdings...</div>
        ) : filteredHoldings && filteredHoldings.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th
                    className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50"
                    onClick={() => handleSort('symbol')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Symbol</span>
                      <ArrowUpDown className="h-4 w-4" />
                    </div>
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Name</th>
                  <th
                    className="text-right py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50"
                    onClick={() => handleSort('quantity')}
                  >
                    <div className="flex items-center justify-end space-x-1">
                      <span>Quantity</span>
                      <ArrowUpDown className="h-4 w-4" />
                    </div>
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Price</th>
                  <th
                    className="text-right py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50"
                    onClick={() => handleSort('value')}
                  >
                    <div className="flex items-center justify-end space-x-1">
                      <span>Value</span>
                      <ArrowUpDown className="h-4 w-4" />
                    </div>
                  </th>
                  <th
                    className="text-right py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50"
                    onClick={() => handleSort('weight')}
                  >
                    <div className="flex items-center justify-end space-x-1">
                      <span>Weight</span>
                      <ArrowUpDown className="h-4 w-4" />
                    </div>
                  </th>
                  <th
                    className="text-right py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50"
                    onClick={() => handleSort('gainLoss')}
                  >
                    <div className="flex items-center justify-end space-x-1">
                      <span>Gain/Loss</span>
                      <ArrowUpDown className="h-4 w-4" />
                    </div>
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">Sector</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {filteredHoldings.map((holding, index) => (
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
                      (holding.unrealized_gain_loss || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
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
            {searchTerm || sectorFilter !== 'all' ? (
              <div>
                <p>No holdings match your filters.</p>
                <button
                  onClick={() => {
                    setSearchTerm('');
                    setSectorFilter('all');
                  }}
                  className="mt-2 text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Clear filters
                </button>
              </div>
            ) : (
              'No holdings data available. Add transactions to see your holdings.'
            )}
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
