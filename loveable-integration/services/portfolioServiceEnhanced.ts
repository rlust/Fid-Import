/**
 * Enhanced Portfolio Service
 * Supports multiple data sources (local, GitHub)
 */

import { dataSource, PortfolioDataSource } from './portfolioDataSource';

export interface Holding {
  id: number;
  snapshot_id: number;
  account_id: string;
  ticker: string;
  company_name: string;
  quantity: number;
  last_price: number;
  value: number;
  sector: string;
  industry: string;
  market_cap: number | null;
  pe_ratio: number | null;
  dividend_yield: number | null;
  portfolio_weight: number;
  account_weight: number;
}

export interface Snapshot {
  id: number;
  timestamp: string;
  total_value: number;
  holdings: Holding[];
}

export interface PortfolioSummary {
  totalValue: number;
  totalHoldings: number;
  timestamp: string;
  snapshotId: number;
  dataSource: string;
  lastRefreshed: string;
}

export interface SectorAllocation {
  sector: string;
  value: number;
  percentage: number;
  holdings: number;
}

export interface TopHolding {
  ticker: string;
  companyName: string;
  value: number;
  weight: number;
}

class EnhancedPortfolioService {
  private dataSource: PortfolioDataSource;
  private data: Snapshot[] | null = null;

  constructor(customDataSource?: PortfolioDataSource) {
    this.dataSource = customDataSource || dataSource;
  }

  /**
   * Initialize and load data
   */
  async initialize(): Promise<void> {
    this.data = await this.dataSource.load();
  }

  /**
   * Refresh data from source
   */
  async refresh(): Promise<void> {
    this.dataSource.clearCache();
    await this.initialize();
  }

  /**
   * Get the latest snapshot
   */
  getLatestSnapshot(): Snapshot | null {
    if (!this.data || this.data.length === 0) {
      return null;
    }
    return this.data[0];
  }

  /**
   * Get portfolio summary with data source info
   */
  getSummary(): PortfolioSummary | null {
    const latest = this.getLatestSnapshot();
    if (!latest) return null;

    const cacheStatus = this.dataSource.getCacheStatus();

    return {
      totalValue: latest.total_value,
      totalHoldings: latest.holdings.length,
      timestamp: latest.timestamp,
      snapshotId: latest.id,
      dataSource: 'GitHub', // Could be dynamic based on config
      lastRefreshed: new Date().toISOString(),
    };
  }

  /**
   * Get all holdings from latest snapshot
   */
  getHoldings(): Holding[] {
    const latest = this.getLatestSnapshot();
    return latest?.holdings || [];
  }

  /**
   * Get top N holdings by value
   */
  getTopHoldings(limit: number = 10): TopHolding[] {
    const holdings = this.getHoldings();

    return holdings
      .filter(h => h.ticker !== 'N/A')
      .sort((a, b) => b.value - a.value)
      .slice(0, limit)
      .map(h => ({
        ticker: h.ticker,
        companyName: h.company_name,
        value: h.value,
        weight: h.portfolio_weight,
      }));
  }

  /**
   * Get sector allocation breakdown
   */
  getSectorAllocation(): SectorAllocation[] {
    const holdings = this.getHoldings();
    const latest = this.getLatestSnapshot();

    if (!latest) return [];

    const sectorMap = new Map<string, { value: number; holdings: number }>();

    holdings.forEach(holding => {
      const sector = holding.sector === 'Unknown' ? 'Other' : holding.sector;
      const current = sectorMap.get(sector) || { value: 0, holdings: 0 };

      sectorMap.set(sector, {
        value: current.value + holding.value,
        holdings: current.holdings + 1,
      });
    });

    const totalValue = latest.total_value;

    return Array.from(sectorMap.entries())
      .map(([sector, data]) => ({
        sector,
        value: data.value,
        percentage: (data.value / totalValue) * 100,
        holdings: data.holdings,
      }))
      .sort((a, b) => b.value - a.value);
  }

  /**
   * Get data freshness info
   */
  getDataFreshness() {
    const latest = this.getLatestSnapshot();
    if (!latest) return null;

    const dataTimestamp = new Date(latest.timestamp);
    const now = new Date();
    const ageInHours = (now.getTime() - dataTimestamp.getTime()) / (1000 * 60 * 60);

    return {
      timestamp: latest.timestamp,
      age: ageInHours,
      ageFormatted: this.formatAge(ageInHours),
      isStale: ageInHours > 24, // Consider stale if > 24 hours old
    };
  }

  private formatAge(hours: number): string {
    if (hours < 1) {
      return `${Math.round(hours * 60)} minutes ago`;
    } else if (hours < 24) {
      return `${Math.round(hours)} hours ago`;
    } else {
      return `${Math.round(hours / 24)} days ago`;
    }
  }

  /**
   * Search holdings
   */
  searchHoldings(query: string): Holding[] {
    const holdings = this.getHoldings();
    const lowerQuery = query.toLowerCase();

    return holdings.filter(h =>
      h.ticker.toLowerCase().includes(lowerQuery) ||
      h.company_name.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Get holdings by sector
   */
  getHoldingsBySector(sector: string): Holding[] {
    const holdings = this.getHoldings();
    return holdings.filter(h => h.sector === sector);
  }

  /**
   * Export data as CSV
   */
  exportToCSV(): string {
    const holdings = this.getHoldings();

    const headers = [
      'Ticker',
      'Company Name',
      'Quantity',
      'Last Price',
      'Value',
      'Portfolio Weight %',
      'Sector',
      'Industry',
    ];

    const rows = holdings.map(h => [
      h.ticker,
      h.company_name,
      h.quantity.toString(),
      h.last_price.toFixed(2),
      h.value.toFixed(2),
      h.portfolio_weight.toFixed(2),
      h.sector,
      h.industry,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');

    return csvContent;
  }

  /**
   * Download data as CSV file
   */
  downloadCSV(filename: string = 'portfolio.csv') {
    const csv = this.exportToCSV();
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
  }
}

// Export singleton instance
export const portfolioService = new EnhancedPortfolioService();

// Export class for custom instances
export default EnhancedPortfolioService;
