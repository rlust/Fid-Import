'use client';

interface CorrelationHeatmapProps {
  data: Record<string, Record<string, number>>;
  title?: string;
}

export function CorrelationHeatmap({ data, title }: CorrelationHeatmapProps) {
  const tickers = Object.keys(data);

  const getColor = (value: number): string => {
    // Correlation ranges from -1 to 1
    // Blue (negative) -> White (0) -> Red (positive)
    if (value > 0.7) return 'bg-red-600';
    if (value > 0.4) return 'bg-red-400';
    if (value > 0.1) return 'bg-red-200';
    if (value > -0.1) return 'bg-gray-100';
    if (value > -0.4) return 'bg-blue-200';
    if (value > -0.7) return 'bg-blue-400';
    return 'bg-blue-600';
  };

  const getTextColor = (value: number): string => {
    if (Math.abs(value) > 0.4) return 'text-white';
    return 'text-gray-900';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {title && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Correlation matrix showing relationship between holdings
          </p>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {/* Empty corner cell */}
              </th>
              {tickers.map((ticker) => (
                <th
                  key={ticker}
                  className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {ticker}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tickers.map((rowTicker, rowIndex) => (
              <tr key={rowTicker}>
                <td className="px-3 py-2 text-xs font-medium text-gray-900 uppercase tracking-wider">
                  {rowTicker}
                </td>
                {tickers.map((colTicker, colIndex) => {
                  const value = data[rowTicker]?.[colTicker] ?? 0;
                  return (
                    <td
                      key={colTicker}
                      className={`px-3 py-2 text-center text-xs font-medium ${getColor(
                        value
                      )} ${getTextColor(value)}`}
                    >
                      {value.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 flex items-center justify-center space-x-6">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-blue-600 rounded"></div>
          <span className="text-xs text-gray-600">Strong Negative</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-gray-100 rounded border border-gray-300"></div>
          <span className="text-xs text-gray-600">No Correlation</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-red-600 rounded"></div>
          <span className="text-xs text-gray-600">Strong Positive</span>
        </div>
      </div>
    </div>
  );
}
