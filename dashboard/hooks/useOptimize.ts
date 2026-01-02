/**
 * React hooks for portfolio optimization using TanStack Query
 */

import { useQuery } from '@tanstack/react-query';
import { optimizeAPI } from '@/lib/api-client';

export function useOptimizeSharpe(days: number = 365, minHoldings: number = 5) {
  return useQuery({
    queryKey: ['optimize', 'sharpe', days, minHoldings],
    queryFn: () => optimizeAPI.optimizeSharpe(days, minHoldings),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useOptimizeMinVolatility(days: number = 365, minHoldings: number = 5) {
  return useQuery({
    queryKey: ['optimize', 'min-volatility', days, minHoldings],
    queryFn: () => optimizeAPI.optimizeMinVolatility(days, minHoldings),
    staleTime: 10 * 60 * 1000,
  });
}

export function useRebalancing(days: number = 365, minHoldings: number = 5) {
  return useQuery({
    queryKey: ['optimize', 'rebalance', days, minHoldings],
    queryFn: () => optimizeAPI.getRebalancing(days, minHoldings),
    staleTime: 10 * 60 * 1000,
  });
}

export function useMonteCarlo(
  days: number = 365,
  minHoldings: number = 5,
  numSimulations: number = 10000,
  timeHorizon: number = 252
) {
  return useQuery({
    queryKey: ['optimize', 'monte-carlo', days, minHoldings, numSimulations, timeHorizon],
    queryFn: () => optimizeAPI.runMonteCarlo(days, minHoldings, numSimulations, timeHorizon),
    staleTime: 15 * 60 * 1000, // 15 minutes (expensive calculation)
    enabled: false, // Only run when explicitly requested
  });
}
