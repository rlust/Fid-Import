/**
 * React hooks for portfolio data using TanStack Query
 */

import { useQuery } from '@tanstack/react-query';
import { portfolioAPI } from '@/lib/api-client';
import type { PortfolioSummary, Holding, SectorAllocation, PortfolioHistory, Snapshot } from '@/types';

export function usePortfolioSummary() {
  return useQuery<PortfolioSummary>({
    queryKey: ['portfolio', 'summary'],
    queryFn: portfolioAPI.getSummary,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useHoldings(limit?: number) {
  return useQuery<Holding[]>({
    queryKey: ['portfolio', 'holdings', limit],
    queryFn: () => portfolioAPI.getHoldings(limit),
    staleTime: 1000 * 60 * 5,
  });
}

export function useTopHoldings(limit: number = 10) {
  return useQuery<Holding[]>({
    queryKey: ['portfolio', 'top-holdings', limit],
    queryFn: () => portfolioAPI.getTopHoldings(limit),
    staleTime: 1000 * 60 * 5,
  });
}

export function useSectorAllocation() {
  return useQuery<SectorAllocation[]>({
    queryKey: ['portfolio', 'sectors'],
    queryFn: portfolioAPI.getSectors,
    staleTime: 1000 * 60 * 5,
  });
}

export function usePortfolioHistory(days: number = 90) {
  return useQuery<PortfolioHistory>({
    queryKey: ['portfolio', 'history', days],
    queryFn: () => portfolioAPI.getHistory(days),
    staleTime: 1000 * 60 * 5,
  });
}

export function useSnapshots(limit: number = 10) {
  return useQuery<Snapshot[]>({
    queryKey: ['portfolio', 'snapshots', limit],
    queryFn: () => portfolioAPI.getSnapshots(limit),
    staleTime: 1000 * 60 * 5,
  });
}
