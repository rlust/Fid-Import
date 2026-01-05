/**
 * API Client for Portfolio Tracker Backend
 * Connects to FastAPI server at localhost:8000
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new APIError(
      errorData.detail || `API request failed: ${response.statusText}`,
      response.status,
      errorData
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

// Portfolio API
export const portfolioAPI = {
  getSummary: (): Promise<any> =>
    fetchAPI('/api/v1/portfolio/summary'),

  getHoldings: (limit?: number): Promise<any> =>
    fetchAPI(`/api/v1/portfolio/holdings${limit ? `?limit=${limit}` : ''}`),

  getTopHoldings: (limit: number = 10): Promise<any> =>
    fetchAPI(`/api/v1/portfolio/top-holdings?limit=${limit}`),

  getSectors: (): Promise<any> =>
    fetchAPI('/api/v1/portfolio/sectors'),

  getHistory: (days: number = 90): Promise<any> =>
    fetchAPI(`/api/v1/portfolio/history?days=${days}`),

  getSnapshots: (limit: number = 10): Promise<any> =>
    fetchAPI(`/api/v1/snapshots?limit=${limit}`),
};

// Transaction API
export const transactionAPI = {
  create: (data: {
    account_id: string;
    ticker: string;
    transaction_type: string;
    transaction_date: string;
    quantity: number;
    total_amount: number;
    price_per_share?: number;
    fees?: number;
    notes?: string;
  }): Promise<any> =>
    fetchAPI('/api/v1/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getAll: (filters?: {
    account_id?: string;
    ticker?: string;
    transaction_type?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<any> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, String(value));
        }
      });
    }
    const query = params.toString();
    return fetchAPI(`/api/v1/transactions${query ? `?${query}` : ''}`);
  },

  getById: (id: number): Promise<any> =>
    fetchAPI(`/api/v1/transactions/${id}`),

  update: (id: number, data: Record<string, any>): Promise<any> =>
    fetchAPI(`/api/v1/transactions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: number): Promise<any> =>
    fetchAPI(`/api/v1/transactions/${id}`, {
      method: 'DELETE',
    }),

  getSummary: (filters?: {
    account_id?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<any> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, String(value));
        }
      });
    }
    const query = params.toString();
    return fetchAPI(`/api/v1/transactions/summary${query ? `?${query}` : ''}`);
  },

  importCSV: async (file: File, dryRun: boolean = true): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${API_BASE_URL}/api/v1/transactions/import?dry_run=${dryRun}`;

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(
        errorData.detail || `CSV import failed: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    return response.json();
  },
};

// Benchmark API
export const benchmarkAPI = {
  getAll: (): Promise<any> =>
    fetchAPI('/api/v1/benchmarks'),

  getByTicker: (ticker: string): Promise<any> =>
    fetchAPI(`/api/v1/benchmarks/${ticker}`),

  getData: (
    ticker: string,
    filters?: {
      start_date?: string;
      end_date?: string;
      days?: number;
    }
  ): Promise<any> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, String(value));
        }
      });
    }
    const query = params.toString();
    return fetchAPI(`/api/v1/benchmarks/${ticker}/data${query ? `?${query}` : ''}`);
  },

  sync: (ticker: string, days: number = 365, replace: boolean = false): Promise<any> =>
    fetchAPI(`/api/v1/benchmarks/${ticker}/sync?days=${days}&replace=${replace}`, {
      method: 'POST',
    }),

  getReturns: (ticker: string, days: number = 30): Promise<any> =>
    fetchAPI(`/api/v1/benchmarks/${ticker}/returns?days=${days}`),
};

// Analytics API
export const analyticsAPI = {
  getPerformance: (days: number = 365): Promise<any> =>
    fetchAPI(`/api/v1/analytics/performance?days=${days}`),

  getPerformanceHistory: (days: number = 365): Promise<any> =>
    fetchAPI(`/api/v1/analytics/performance/history?days=${days}`),

  getHoldingPerformance: (ticker: string, days: number = 365): Promise<any> =>
    fetchAPI(`/api/v1/analytics/performance/holding/${ticker}?days=${days}`),

  getAttribution: (days: number = 30): Promise<any> =>
    fetchAPI(`/api/v1/analytics/attribution?days=${days}`),

  getSectorAttribution: (days: number = 30): Promise<any> =>
    fetchAPI(`/api/v1/analytics/attribution/sector?days=${days}`),

  getTopContributors: (days: number = 30, limit: number = 10): Promise<any> =>
    fetchAPI(`/api/v1/analytics/contributors?days=${days}&limit=${limit}`),
};

// Risk Analytics API
export const riskAPI = {
  getComprehensive: (days: number = 365): Promise<any> =>
    fetchAPI(`/api/v1/risk/comprehensive?days=${days}`),

  getVolatility: (days: number = 365): Promise<any> =>
    fetchAPI(`/api/v1/risk/volatility?days=${days}`),

  getSharpeRatio: (days: number = 365): Promise<any> =>
    fetchAPI(`/api/v1/risk/sharpe?days=${days}`),

  getBeta: (days: number = 365, benchmark: string = '^GSPC'): Promise<any> =>
    fetchAPI(`/api/v1/risk/beta?days=${days}&benchmark=${benchmark}`),

  getValueAtRisk: (days: number = 365, confidence: number = 0.95): Promise<any> =>
    fetchAPI(`/api/v1/risk/var?days=${days}&confidence=${confidence}`),

  getMaxDrawdown: (days: number = 365): Promise<any> =>
    fetchAPI(`/api/v1/risk/drawdown?days=${days}`),

  getCorrelationMatrix: (days: number = 365, minHoldings: number = 5): Promise<any> =>
    fetchAPI(`/api/v1/risk/correlation?days=${days}&min_holdings=${minHoldings}`),
};

// Portfolio Optimization API
export const optimizeAPI = {
  optimizeSharpe: (days: number = 365, minHoldings: number = 5): Promise<any> =>
    fetchAPI(`/api/v1/optimize/sharpe?days=${days}&min_holdings=${minHoldings}`),

  optimizeMinVolatility: (days: number = 365, minHoldings: number = 5): Promise<any> =>
    fetchAPI(`/api/v1/optimize/min-volatility?days=${days}&min_holdings=${minHoldings}`),

  getEfficientFrontier: (days: number = 365, minHoldings: number = 5, numPoints: number = 50): Promise<any> =>
    fetchAPI(`/api/v1/optimize/efficient-frontier?days=${days}&min_holdings=${minHoldings}&num_points=${numPoints}`),

  runMonteCarlo: (
    days: number = 365,
    minHoldings: number = 5,
    numSimulations: number = 10000,
    timeHorizon: number = 252
  ): Promise<any> =>
    fetchAPI(
      `/api/v1/optimize/monte-carlo?days=${days}&min_holdings=${minHoldings}&num_simulations=${numSimulations}&time_horizon=${timeHorizon}`
    ),

  getRebalancing: (days: number = 365, minHoldings: number = 5): Promise<any> =>
    fetchAPI(`/api/v1/optimize/rebalance?days=${days}&min_holdings=${minHoldings}`),
};

// Health check
export const healthAPI = {
  check: (): Promise<any> => fetchAPI('/health'),
};
