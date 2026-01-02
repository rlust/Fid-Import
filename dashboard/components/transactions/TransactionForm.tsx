'use client';

import { useState } from 'react';
import { useCreateTransaction } from '@/hooks/useTransactions';

interface TransactionFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function TransactionForm({ onSuccess, onCancel }: TransactionFormProps) {
  const createTransaction = useCreateTransaction();
  const [formData, setFormData] = useState({
    account_id: '',
    ticker: '',
    transaction_type: 'BUY',
    transaction_date: new Date().toISOString().split('T')[0],
    quantity: '',
    total_amount: '',
    price_per_share: '',
    fees: '',
    notes: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await createTransaction.mutateAsync({
        account_id: formData.account_id,
        ticker: formData.ticker.toUpperCase(),
        transaction_type: formData.transaction_type,
        transaction_date: formData.transaction_date,
        quantity: parseFloat(formData.quantity),
        total_amount: parseFloat(formData.total_amount),
        price_per_share: formData.price_per_share ? parseFloat(formData.price_per_share) : undefined,
        fees: formData.fees ? parseFloat(formData.fees) : undefined,
        notes: formData.notes || undefined,
      });

      // Reset form
      setFormData({
        account_id: '',
        ticker: '',
        transaction_type: 'BUY',
        transaction_date: new Date().toISOString().split('T')[0],
        quantity: '',
        total_amount: '',
        price_per_share: '',
        fees: '',
        notes: '',
      });

      if (onSuccess) onSuccess();
    } catch (error) {
      console.error('Failed to create transaction:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Auto-calculate price per share if quantity and total amount are provided
    if (name === 'quantity' || name === 'total_amount') {
      const quantity = name === 'quantity' ? parseFloat(value) : parseFloat(formData.quantity);
      const totalAmount = name === 'total_amount' ? parseFloat(value) : parseFloat(formData.total_amount);

      if (quantity && totalAmount && quantity > 0) {
        const pricePerShare = (totalAmount / quantity).toFixed(4);
        setFormData(prev => ({ ...prev, price_per_share: pricePerShare }));
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Account ID */}
        <div>
          <label htmlFor="account_id" className="block text-sm font-medium text-gray-700 mb-2">
            Account ID
          </label>
          <input
            type="text"
            id="account_id"
            name="account_id"
            required
            value={formData.account_id}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="e.g., X12345678"
          />
        </div>

        {/* Ticker */}
        <div>
          <label htmlFor="ticker" className="block text-sm font-medium text-gray-700 mb-2">
            Ticker Symbol
          </label>
          <input
            type="text"
            id="ticker"
            name="ticker"
            required
            value={formData.ticker}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent uppercase"
            placeholder="e.g., AAPL"
          />
        </div>

        {/* Transaction Type */}
        <div>
          <label htmlFor="transaction_type" className="block text-sm font-medium text-gray-700 mb-2">
            Transaction Type
          </label>
          <select
            id="transaction_type"
            name="transaction_type"
            required
            value={formData.transaction_type}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="BUY">Buy</option>
            <option value="SELL">Sell</option>
            <option value="DIVIDEND">Dividend</option>
            <option value="FEE">Fee</option>
            <option value="SPLIT">Stock Split</option>
            <option value="TRANSFER">Transfer</option>
          </select>
        </div>

        {/* Transaction Date */}
        <div>
          <label htmlFor="transaction_date" className="block text-sm font-medium text-gray-700 mb-2">
            Date
          </label>
          <input
            type="date"
            id="transaction_date"
            name="transaction_date"
            required
            value={formData.transaction_date}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Quantity */}
        <div>
          <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-2">
            Quantity
          </label>
          <input
            type="number"
            id="quantity"
            name="quantity"
            required
            step="0.0001"
            value={formData.quantity}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="0.00"
          />
        </div>

        {/* Total Amount */}
        <div>
          <label htmlFor="total_amount" className="block text-sm font-medium text-gray-700 mb-2">
            Total Amount ($)
          </label>
          <input
            type="number"
            id="total_amount"
            name="total_amount"
            required
            step="0.01"
            value={formData.total_amount}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="0.00"
          />
        </div>

        {/* Price Per Share (auto-calculated) */}
        <div>
          <label htmlFor="price_per_share" className="block text-sm font-medium text-gray-700 mb-2">
            Price Per Share ($)
          </label>
          <input
            type="number"
            id="price_per_share"
            name="price_per_share"
            step="0.0001"
            value={formData.price_per_share}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50"
            placeholder="Auto-calculated"
          />
        </div>

        {/* Fees */}
        <div>
          <label htmlFor="fees" className="block text-sm font-medium text-gray-700 mb-2">
            Fees ($)
          </label>
          <input
            type="number"
            id="fees"
            name="fees"
            step="0.01"
            value={formData.fees}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="0.00"
          />
        </div>
      </div>

      {/* Notes */}
      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
          Notes (optional)
        </label>
        <textarea
          id="notes"
          name="notes"
          rows={3}
          value={formData.notes}
          onChange={handleChange}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Add any additional notes..."
        />
      </div>

      {/* Error Message */}
      {createTransaction.isError && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4">
          <p className="text-sm text-red-700">
            Failed to create transaction. Please check your input and try again.
          </p>
        </div>
      )}

      {/* Buttons */}
      <div className="flex justify-end space-x-4">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={createTransaction.isPending}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
        >
          {createTransaction.isPending ? 'Creating...' : 'Create Transaction'}
        </button>
      </div>
    </form>
  );
}
