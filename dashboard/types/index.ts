/**
 * TypeScript type definitions for Portfolio Tracker
 */

export interface PortfolioSummary {
  total_value: number;
  total_holdings: number;
  total_gain_loss?: number;
  total_return_percent?: number;
  last_updated: string;
}

export interface Holding {
  symbol: string;
  company_name?: string;
  quantity: number;
  last_price: number;
  value: number;
  cost_basis?: number;
  gain_loss?: number;
  gain_loss_percent?: number;
  portfolio_weight?: number;
  sector?: string;
  industry?: string;
}

export interface SectorAllocation {
  sector: string;
  value: number;
  percentage: number;
}

export interface Snapshot {
  id: number;
  timestamp: string;
  total_value: number;
}

export interface PortfolioHistory {
  data: Array<{
    timestamp: string;
    total_value: number;
  }>;
  period_days: number;
  data_points: number;
}

export interface Transaction {
  id: number;
  account_id: string;
  ticker: string;
  transaction_type: 'BUY' | 'SELL' | 'DIVIDEND' | 'FEE' | 'SPLIT' | 'TRANSFER';
  transaction_date: string;
  quantity: number;
  price_per_share?: number;
  total_amount: number;
  fees: number;
  notes?: string;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionCreate {
  account_id: string;
  ticker: string;
  transaction_type: string;
  transaction_date: string;
  quantity: number;
  total_amount: number;
  price_per_share?: number;
  fees?: number;
  notes?: string;
}

export interface TransactionSummary {
  total_transactions: number;
  by_type: Record<string, number>;
  total_invested: number;
  total_proceeds: number;
  total_dividends: number;
  total_fees: number;
}

export interface Benchmark {
  id: number;
  name: string;
  ticker: string;
  description?: string;
  is_active: boolean;
}

export interface BenchmarkData {
  date: string;
  close_price: number;
  open_price?: number;
  high_price?: number;
  low_price?: number;
  volume?: number;
}

export interface BenchmarkReturns {
  ticker: string;
  period_days: number;
  start_date: string;
  end_date: string;
  start_price: number;
  end_price: number;
  return_percent: number;
  data_points: number;
}
