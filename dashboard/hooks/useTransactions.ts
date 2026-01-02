/**
 * React hooks for transaction data using TanStack Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { transactionAPI } from '@/lib/api-client';

export function useTransactions(filters?: {
  account_id?: string;
  ticker?: string;
  transaction_type?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => transactionAPI.getAll(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useTransaction(id: number) {
  return useQuery({
    queryKey: ['transaction', id],
    queryFn: () => transactionAPI.getById(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: transactionAPI.create,
    onSuccess: () => {
      // Invalidate and refetch transactions
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      // Also invalidate portfolio data since it depends on transactions
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
  });
}

export function useUpdateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, any> }) =>
      transactionAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
  });
}

export function useDeleteTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: transactionAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
  });
}

export function useTransactionSummary(filters?: {
  account_id?: string;
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ['transaction-summary', filters],
    queryFn: () => transactionAPI.getSummary(filters),
    staleTime: 5 * 60 * 1000,
  });
}
