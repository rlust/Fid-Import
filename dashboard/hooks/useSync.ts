/**
 * React hooks for portfolio sync operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { syncAPI } from '@/lib/api-client';

export function useSyncStatus() {
  return useQuery({
    queryKey: ['sync-status'],
    queryFn: () => syncAPI.getStatus(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  });
}

export function useManualSync() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => syncAPI.triggerManualSync(),
    onSuccess: () => {
      // Invalidate sync status to refresh
      queryClient.invalidateQueries({ queryKey: ['sync-status'] });
      // Invalidate portfolio data to refresh after sync completes
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['portfolio'] });
        queryClient.invalidateQueries({ queryKey: ['holdings'] });
      }, 5000); // Wait 5 seconds for sync to potentially complete
    },
  });
}
