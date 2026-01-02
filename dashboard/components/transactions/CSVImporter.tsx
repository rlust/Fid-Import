'use client';

import { useState, useRef } from 'react';
import { transactionAPI } from '@/lib/api-client';
import { Upload, FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export function CSVImporter({ onSuccess }: { onSuccess?: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (selectedFile: File) => {
    if (!selectedFile.name.endsWith('.csv')) {
      setError('Please select a CSV file');
      return;
    }

    setFile(selectedFile);
    setError(null);
    setIsUploading(true);

    try {
      // Preview the import (dry run)
      const result = await transactionAPI.importCSV(selectedFile, true);
      setPreview(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to preview CSV');
      setPreview(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleImport = async () => {
    if (!file) return;

    setIsImporting(true);
    setError(null);

    try {
      // Actually import (dry_run=false)
      const result = await transactionAPI.importCSV(file, false);

      if (result.success) {
        // Reset state
        setFile(null);
        setPreview(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        if (onSuccess) onSuccess();
      } else {
        setError(`Import completed with errors: ${result.errors.join(', ')}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setIsImporting(false);
    }
  };

  const handleCancel = () => {
    setFile(null);
    setPreview(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6">
      {/* File Upload Area */}
      {!file && (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer hover:border-blue-400 transition-colors"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileInputChange}
            className="hidden"
          />
          <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">
            Drop your CSV file here or click to browse
          </p>
          <p className="text-sm text-gray-500">
            Supports Fidelity transaction export files (.csv)
          </p>
        </div>
      )}

      {/* Preview */}
      {isUploading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <p className="text-blue-900">Analyzing CSV file...</p>
          </div>
        </div>
      )}

      {preview && file && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
          {/* File Info */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="h-8 w-8 text-blue-600" />
              <div>
                <p className="font-semibold text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
            <button
              onClick={handleCancel}
              className="text-gray-500 hover:text-gray-700"
            >
              <XCircle className="h-6 w-6" />
            </button>
          </div>

          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500 mb-1">Total Rows</p>
              <p className="text-2xl font-semibold text-gray-900">
                {preview.total_rows}
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-gray-500 mb-1">Valid</p>
              <p className="text-2xl font-semibold text-green-600">
                {preview.valid_transactions}
              </p>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <p className="text-sm text-gray-500 mb-1">Errors</p>
              <p className="text-2xl font-semibold text-red-600">
                {preview.errors?.length || 0}
              </p>
            </div>
          </div>

          {/* Errors */}
          {preview.errors && preview.errors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-red-900 mb-2">
                    Import Errors ({preview.errors.length})
                  </p>
                  <ul className="text-sm text-red-700 space-y-1 list-disc list-inside">
                    {preview.errors.slice(0, 5).map((error: string, i: number) => (
                      <li key={i}>{error}</li>
                    ))}
                    {preview.errors.length > 5 && (
                      <li className="text-red-600">
                        ...and {preview.errors.length - 5} more errors
                      </li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Preview Transactions */}
          {preview.preview && preview.preview.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">
                Preview (First 10 Transactions)
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium text-gray-600">Date</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-600">Type</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-600">Symbol</th>
                      <th className="px-4 py-2 text-right font-medium text-gray-600">Quantity</th>
                      <th className="px-4 py-2 text-right font-medium text-gray-600">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {preview.preview.map((txn: any, i: number) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-2">{txn.transaction_date}</td>
                        <td className="px-4 py-2">
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                            {txn.transaction_type}
                          </span>
                        </td>
                        <td className="px-4 py-2 font-medium">{txn.ticker}</td>
                        <td className="px-4 py-2 text-right">{txn.quantity?.toFixed(2)}</td>
                        <td className="px-4 py-2 text-right">
                          ${txn.total_amount?.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200">
            <button
              onClick={handleCancel}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleImport}
              disabled={isImporting || (preview.errors && preview.errors.length > 0)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors flex items-center space-x-2"
            >
              {isImporting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Importing...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4" />
                  <span>Import {preview.valid_transactions} Transactions</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && !preview && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <div>
              <p className="font-medium text-red-900">Error</p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
