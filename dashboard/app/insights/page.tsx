'use client';

import { Construction } from 'lucide-react';

export default function InsightsPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AI-Powered Insights</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Intelligent portfolio recommendations and market insights
        </p>
      </div>

      {/* Coming Soon */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12">
        <div className="flex flex-col items-center justify-center text-center space-y-4">
          <div className="rounded-full bg-blue-100 dark:bg-blue-900/30 p-6">
            <Construction className="h-12 w-12 text-blue-600 dark:text-blue-400" />
          </div>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
            Coming Soon
          </h2>
          <p className="text-gray-600 dark:text-gray-400 max-w-md">
            We're working on AI-powered insights that will help you make smarter investment decisions.
            Stay tuned for features like:
          </p>
          <ul className="text-left text-gray-600 dark:text-gray-400 space-y-2">
            <li className="flex items-center space-x-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>Portfolio rebalancing recommendations</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>Risk alerts and warnings</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>Tax optimization strategies</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>Market trend analysis</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>Personalized investment suggestions</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
