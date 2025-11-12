/**
 * React Hook for Portfolio Data
 * Provides easy access to portfolio data with React Query integration
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import {
  portfolioService,
  PortfolioSummary,
  Holding,
  SectorAllocation,
  TopHolding,
  Snapshot,
} from '@/services/portfolioService';

/**
 * Hook to get portfolio summary
 */
export function usePortfolioSummary(): UseQueryResult<PortfolioSummary | null> {
  return useQuery({
    queryKey: ['portfolio', 'summary'],
    queryFn: () => portfolioService.getSummary(),
    staleTime: 1000 * 60 * 60, // 1 hour
    gcTime: 1000 * 60 * 60 * 24, // 24 hours (formerly cacheTime)
  });
}

/**
 * Hook to get all holdings
 */
export function useHoldings(): UseQueryResult<Holding[]> {
  return useQuery({
    queryKey: ['portfolio', 'holdings'],
    queryFn: () => portfolioService.getHoldings(),
    staleTime: 1000 * 60 * 60,
  });
}

/**
 * Hook to get top holdings
 */
export function useTopHoldings(limit: number = 10): UseQueryResult<TopHolding[]> {
  return useQuery({
    queryKey: ['portfolio', 'top-holdings', limit],
    queryFn: () => portfolioService.getTopHoldings(limit),
    staleTime: 1000 * 60 * 60,
  });
}

/**
 * Hook to get sector allocation
 */
export function useSectorAllocation(): UseQueryResult<SectorAllocation[]> {
  return useQuery({
    queryKey: ['portfolio', 'sector-allocation'],
    queryFn: () => portfolioService.getSectorAllocation(),
    staleTime: 1000 * 60 * 60,
  });
}

/**
 * Hook to get holdings by sector
 */
export function useHoldingsBySector(sector: string): UseQueryResult<Holding[]> {
  return useQuery({
    queryKey: ['portfolio', 'holdings-by-sector', sector],
    queryFn: () => portfolioService.getHoldingsBySector(sector),
    staleTime: 1000 * 60 * 60,
    enabled: !!sector, // Only run if sector is provided
  });
}

/**
 * Hook to search holdings
 */
export function useSearchHoldings(query: string): UseQueryResult<Holding[]> {
  return useQuery({
    queryKey: ['portfolio', 'search', query],
    queryFn: () => portfolioService.searchHoldings(query),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: query.length >= 2, // Only search with 2+ characters
  });
}

/**
 * Hook to get portfolio statistics
 */
export function usePortfolioStatistics() {
  return useQuery({
    queryKey: ['portfolio', 'statistics'],
    queryFn: () => portfolioService.getStatistics(),
    staleTime: 1000 * 60 * 60,
  });
}

/**
 * Hook to get latest snapshot
 */
export function useLatestSnapshot(): UseQueryResult<Snapshot | null> {
  return useQuery({
    queryKey: ['portfolio', 'latest-snapshot'],
    queryFn: () => portfolioService.getLatestSnapshot(),
    staleTime: 1000 * 60 * 60,
  });
}

/**
 * Hook to get historical comparison
 */
export function useHistoricalComparison() {
  return useQuery({
    queryKey: ['portfolio', 'historical-comparison'],
    queryFn: () => portfolioService.getHistoricalComparison(),
    staleTime: 1000 * 60 * 60,
  });
}

/**
 * Hook to get all sectors
 */
export function useSectors(): UseQueryResult<string[]> {
  return useQuery({
    queryKey: ['portfolio', 'sectors'],
    queryFn: () => portfolioService.getSectors(),
    staleTime: 1000 * 60 * 60,
  });
}

/**
 * Combined hook for dashboard data
 * Fetches all necessary data for main dashboard
 */
export function useDashboardData() {
  const summary = usePortfolioSummary();
  const topHoldings = useTopHoldings(10);
  const sectorAllocation = useSectorAllocation();
  const statistics = usePortfolioStatistics();

  return {
    summary: summary.data,
    topHoldings: topHoldings.data,
    sectorAllocation: sectorAllocation.data,
    statistics: statistics.data,
    isLoading:
      summary.isLoading ||
      topHoldings.isLoading ||
      sectorAllocation.isLoading ||
      statistics.isLoading,
    isError:
      summary.isError ||
      topHoldings.isError ||
      sectorAllocation.isError ||
      statistics.isError,
    error: summary.error || topHoldings.error || sectorAllocation.error || statistics.error,
  };
}

/**
 * Hook for downloading CSV
 */
export function useDownloadCSV() {
  return () => {
    const date = new Date().toISOString().split('T')[0];
    portfolioService.downloadCSV(`portfolio-${date}.csv`);
  };
}
