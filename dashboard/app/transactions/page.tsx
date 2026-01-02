'use client';

import { useState } from 'react';
import { TransactionForm } from '@/components/transactions/TransactionForm';
import { TransactionTable } from '@/components/transactions/TransactionTable';
import { CSVImporter } from '@/components/transactions/CSVImporter';
import { Plus, List, Upload, FileText } from 'lucide-react';

type ViewMode = 'list' | 'add' | 'import';

export default function TransactionsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
          <p className="mt-2 text-gray-600">
            Manage your investment transactions
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setViewMode('import')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              viewMode === 'import'
                ? 'bg-green-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Upload className="h-5 w-5" />
            <span>Import CSV</span>
          </button>
          <button
            onClick={() => setViewMode(viewMode === 'add' ? 'list' : 'add')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              viewMode === 'add'
                ? 'bg-blue-600 text-white'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {viewMode === 'add' ? (
              <>
                <List className="h-5 w-5" />
                <span>View List</span>
              </>
            ) : (
              <>
                <Plus className="h-5 w-5" />
                <span>Add Transaction</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* CSV Import */}
      {viewMode === 'import' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-6">
            <FileText className="h-6 w-6 text-gray-900" />
            <h2 className="text-lg font-semibold text-gray-900">
              Import Transactions from CSV
            </h2>
          </div>
          <CSVImporter
            onSuccess={() => {
              setViewMode('list');
            }}
          />
        </div>
      )}

      {/* Add Transaction Form */}
      {viewMode === 'add' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">
            Add New Transaction
          </h2>
          <TransactionForm
            onSuccess={() => {
              setViewMode('list');
            }}
            onCancel={() => setViewMode('list')}
          />
        </div>
      )}

      {/* Transaction List */}
      {viewMode === 'list' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Transaction History
          </h2>
          <TransactionTable />
        </div>
      )}
    </div>
  );
}
