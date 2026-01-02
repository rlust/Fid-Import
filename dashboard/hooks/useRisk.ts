/**
 * React hooks for risk analytics data using TanStack Query
 */

import { useQuery } from '@tanstack/react-query';
import { riskAPI } from '@/lib/api-client';

export function useComprehensiveRisk(days: number = 365) {
  return useQuery({
    queryKey: ['risk', 'comprehensive', days],
    queryFn: () => riskAPI.getComprehensive(days),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useVolatility(days: number = 365) {
  return useQuery({
    queryKey: ['risk', 'volatility', days],
    queryFn: () => riskAPI.getVolatility(days),
    staleTime: 5 * 60 * 1000,
  });
}

export function useSharpeRatio(days: number = 365) {
  return useQuery({
    queryKey: ['risk', 'sharpe', days],
    queryFn: () => riskAPI.getSharpeRatio(days),
    staleTime: 5 * 60 * 1000,
  });
}

export function useBeta(days: number = 365, benchmark: string = '^GSPC') {
  return useQuery({
    queryKey: ['risk', 'beta', days, benchmark],
    queryFn: () => riskAPI.getBeta(days, benchmark),
    staleTime: 5 * 60 * 1000,
  });
}

export function useValueAtRisk(days: number = 365, confidence: number = 0.95) {
  return useQuery({
    queryKey: ['risk', 'var', days, confidence],
    queryFn: () => riskAPI.getValueAtRisk(days, confidence),
    staleTime: 5 * 60 * 1000,
  });
}

export function useMaxDrawdown(days: number = 365) {
  return useQuery({
    queryKey: ['risk', 'drawdown', days],
    queryFn: () => riskAPI.getMaxDrawdown(days),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCorrelationMatrix(days: number = 365, minHoldings: number = 5) {
  return useQuery({
    queryKey: ['risk', 'correlation', days, minHoldings],
    queryFn: () => riskAPI.getCorrelationMatrix(days, minHoldings),
    staleTime: 5 * 60 * 1000,
  });
}
