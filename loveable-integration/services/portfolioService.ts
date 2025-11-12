/**
 * Portfolio Service
 * Handles loading and processing portfolio data from JSON file
 */

import portfolioData from '@/data/portfolio-latest.json';

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
  change?: number;
}

class PortfolioService {
  private data: Snapshot[];

  constructor() {
    // Cast the imported JSON to the correct type
    this.data = portfolioData as unknown as Snapshot[];
  }

  /**
   * Get the latest snapshot
   */
  getLatestSnapshot(): Snapshot | null {
    if (!this.data || this.data.length === 0) {
      return null;
    }
    return this.data[0]; // Assuming data is sorted with latest first
  }

  /**
   * Get portfolio summary
   */
  getSummary(): PortfolioSummary | null {
    const latest = this.getLatestSnapshot();
    if (!latest) return null;

    return {
      totalValue: latest.total_value,
      totalHoldings: latest.holdings.length,
      timestamp: latest.timestamp,
      snapshotId: latest.id,
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
      .filter(h => h.ticker !== 'N/A') // Exclude cash positions
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

    // Group by sector
    const sectorMap = new Map<string, { value: number; holdings: number }>();

    holdings.forEach(holding => {
      const sector = holding.sector === 'Unknown' ? 'Other' : holding.sector;
      const current = sectorMap.get(sector) || { value: 0, holdings: 0 };

      sectorMap.set(sector, {
        value: current.value + holding.value,
        holdings: current.holdings + 1,
      });
    });

    // Convert to array and calculate percentages
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
   * Get holdings by sector
   */
  getHoldingsBySector(sector: string): Holding[] {
    const holdings = this.getHoldings();
    return holdings.filter(h => h.sector === sector);
  }

  /**
   * Search holdings by ticker or company name
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
   * Get portfolio statistics
   */
  getStatistics() {
    const holdings = this.getHoldings();
    const latest = this.getLatestSnapshot();

    if (!latest) return null;

    const cashHoldings = holdings.filter(h => h.sector === 'Cash');
    const stockHoldings = holdings.filter(h => h.sector !== 'Cash');

    const totalCash = cashHoldings.reduce((sum, h) => sum + h.value, 0);
    const totalStocks = stockHoldings.reduce((sum, h) => sum + h.value, 0);

    // Calculate average metrics
    const avgPrice = stockHoldings.reduce((sum, h) => sum + h.last_price, 0) / stockHoldings.length;
    const avgWeight = stockHoldings.reduce((sum, h) => sum + h.portfolio_weight, 0) / stockHoldings.length;

    return {
      totalValue: latest.total_value,
      totalHoldings: holdings.length,
      stockHoldings: stockHoldings.length,
      cashHoldings: cashHoldings.length,
      totalCash,
      totalStocks,
      cashPercentage: (totalCash / latest.total_value) * 100,
      stocksPercentage: (totalStocks / latest.total_value) * 100,
      averageStockPrice: avgPrice,
      averageWeight: avgWeight,
      largestHolding: stockHoldings[0],
      timestamp: latest.timestamp,
    };
  }

  /**
   * Get all unique sectors
   */
  getSectors(): string[] {
    const holdings = this.getHoldings();
    const sectors = new Set(holdings.map(h => h.sector));
    return Array.from(sectors).filter(s => s !== 'Unknown').sort();
  }

  /**
   * Get historical comparison (if multiple snapshots available)
   */
  getHistoricalComparison() {
    if (this.data.length < 2) {
      return null;
    }

    const latest = this.data[0];
    const previous = this.data[1];

    const valueChange = latest.total_value - previous.total_value;
    const percentChange = (valueChange / previous.total_value) * 100;
    const holdingsChange = latest.holdings.length - previous.holdings.length;

    return {
      currentValue: latest.total_value,
      previousValue: previous.total_value,
      valueChange,
      percentChange,
      currentHoldings: latest.holdings.length,
      previousHoldings: previous.holdings.length,
      holdingsChange,
      currentDate: latest.timestamp,
      previousDate: previous.timestamp,
    };
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
export const portfolioService = new PortfolioService();

// Export class for testing
export default PortfolioService;
