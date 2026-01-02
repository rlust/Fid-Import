/**
 * React hooks for performance analytics data
 */

import { useQuery } from '@tanstack/react-query';
import { analyticsAPI } from '@/lib/api-client';

export function usePerformance(days: number = 365) {
  return useQuery({
    queryKey: ['performance', days],
    queryFn: () => analyticsAPI.getPerformance(days),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useHoldingPerformance(ticker: string, days: number = 365) {
  return useQuery({
    queryKey: ['holding-performance', ticker, days],
    queryFn: () => analyticsAPI.getHoldingPerformance(ticker, days),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  });
}

export function useAttribution(days: number = 30) {
  return useQuery({
    queryKey: ['attribution', days],
    queryFn: () => analyticsAPI.getAttribution(days),
    staleTime: 5 * 60 * 1000,
  });
}

export function useSectorAttribution(days: number = 30) {
  return useQuery({
    queryKey: ['sector-attribution', days],
    queryFn: () => analyticsAPI.getSectorAttribution(days),
    staleTime: 5 * 60 * 1000,
  });
}

export function useTopContributors(days: number = 30, limit: number = 10) {
  return useQuery({
    queryKey: ['top-contributors', days, limit],
    queryFn: () => analyticsAPI.getTopContributors(days, limit),
    staleTime: 5 * 60 * 1000,
  });
}
