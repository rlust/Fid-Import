'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatCurrency, formatDate } from '@/lib/formatters';

interface TimelineDataPoint {
  timestamp: string;
  total_value: number;
}

interface PortfolioTimelineProps {
  data?: {
    data: TimelineDataPoint[];
    period_days: number;
    data_points: number;
  };
  isLoading?: boolean;
}

export function PortfolioTimeline({ data, isLoading }: PortfolioTimelineProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8">
        <div className="text-center text-gray-500">Loading chart data...</div>
      </div>
    );
  }

  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8">
        <div className="text-center text-gray-500">
          No historical data available. Data will appear as snapshots are created over time.
        </div>
      </div>
    );
  }

  // Transform data for Recharts
  const chartData = data.data.map((point) => ({
    date: point.timestamp,
    value: point.total_value,
    formattedDate: formatDate(point.timestamp),
  }));

  // Calculate min and max for Y-axis domain
  const values = chartData.map(d => d.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const padding = (maxValue - minValue) * 0.1; // 10% padding

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Portfolio Performance</h2>
        <p className="mt-1 text-sm text-gray-500">
          Last {data.period_days} days • {data.data_points} data points
        </p>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="formattedDate"
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              tickFormatter={(value) => {
                // Show fewer labels on mobile
                const parts = value.split(' ');
                return parts.length >= 2 ? `${parts[0]} ${parts[1]}` : value;
              }}
            />
            <YAxis
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              tickFormatter={(value) => {
                // Format as compact currency
                if (value >= 1000000) {
                  return `$${(value / 1000000).toFixed(1)}M`;
                }
                if (value >= 1000) {
                  return `$${(value / 1000).toFixed(0)}K`;
                }
                return `$${value}`;
              }}
              domain={[
                Math.floor((minValue - padding) / 1000) * 1000,
                Math.ceil((maxValue + padding) / 1000) * 1000,
              ]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '12px',
              }}
              formatter={(value: any) => [formatCurrency(value), 'Portfolio Value']}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Legend
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
            />
            <Line
              type="monotone"
              dataKey="value"
              name="Portfolio Value"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-gray-200">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Starting Value</p>
          <p className="mt-1 text-lg font-semibold text-gray-900">
            {formatCurrency(chartData[0]?.value)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Current Value</p>
          <p className="mt-1 text-lg font-semibold text-gray-900">
            {formatCurrency(chartData[chartData.length - 1]?.value)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Change</p>
          <p className="mt-1 text-lg font-semibold text-gray-900">
            {formatCurrency(
              chartData[chartData.length - 1]?.value - chartData[0]?.value
            )}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Return %</p>
          <p
            className={`mt-1 text-lg font-semibold ${
              chartData[chartData.length - 1]?.value >= chartData[0]?.value
                ? 'text-green-600'
                : 'text-red-600'
            }`}
          >
            {(
              ((chartData[chartData.length - 1]?.value - chartData[0]?.value) /
                chartData[0]?.value) *
              100
            ).toFixed(2)}
            %
          </p>
        </div>
      </div>
    </div>
  );
}
