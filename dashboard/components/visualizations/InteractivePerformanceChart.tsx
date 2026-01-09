'use client';

import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
  ReferenceLine,
} from 'recharts';
import { formatCurrency, formatPercent, formatDate } from '@/lib/formatters';

interface ChartDataPoint {
  date: string;
  value: number;
  benchmark?: number;
  return?: number;
}

interface InteractivePerformanceChartProps {
  data: ChartDataPoint[];
  title?: string;
  showBenchmark?: boolean;
  showReturns?: boolean;
  height?: number;
}

export function InteractivePerformanceChart({
  data,
  title,
  showBenchmark = false,
  showReturns = false,
  height = 400,
}: InteractivePerformanceChartProps) {
  const [brushStartIndex, setBrushStartIndex] = useState<number | undefined>(undefined);
  const [brushEndIndex, setBrushEndIndex] = useState<number | undefined>(undefined);

  // Detect if data is normalized (benchmark comparison mode)
  const isNormalized = data.length > 0 && data[0].value < 1000;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="bg-white px-4 py-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-900 mb-2">{formatDate(label)}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center justify-between space-x-4">
            <span className="text-sm" style={{ color: entry.color }}>
              {entry.name}:
            </span>
            <span className="text-sm font-medium" style={{ color: entry.color }}>
              {entry.dataKey === 'return'
                ? formatPercent(entry.value)
                : isNormalized
                ? `${entry.value.toFixed(2)}`
                : formatCurrency(entry.value)}
            </span>
          </div>
        ))}
      </div>
    );
  };

  const handleBrushChange = (range: any) => {
    if (range && range.startIndex !== undefined && range.endIndex !== undefined) {
      setBrushStartIndex(range.startIndex);
      setBrushEndIndex(range.endIndex);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {title && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600 mt-1">
            Use the brush below to zoom into specific time periods
          </p>
        </div>
      )}

      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

          <XAxis
            dataKey="date"
            tickFormatter={(date) => {
              const d = new Date(date);
              return `${d.getMonth() + 1}/${d.getDate()}`;
            }}
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />

          <YAxis
            yAxisId="left"
            tickFormatter={(value) =>
              isNormalized ? value.toFixed(0) : `$${(value / 1000).toFixed(0)}k`
            }
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />

          {showReturns && (
            <YAxis
              yAxisId="right"
              orientation="right"
              tickFormatter={(value) => `${value.toFixed(1)}%`}
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
          )}

          <Tooltip content={<CustomTooltip />} />

          <Legend
            wrapperStyle={{ fontSize: '14px', paddingTop: '10px' }}
            iconType="line"
          />

          <ReferenceLine y={0} yAxisId="left" stroke="#9ca3af" strokeDasharray="3 3" />

          <Line
            yAxisId="left"
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name={isNormalized ? "Portfolio" : "Portfolio Value"}
            activeDot={{ r: 6 }}
          />

          {showBenchmark && (
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="benchmark"
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="Benchmark"
              activeDot={{ r: 6 }}
            />
          )}

          {showReturns && (
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="return"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              name="Return %"
              activeDot={{ r: 6 }}
            />
          )}

          <Brush
            dataKey="date"
            height={30}
            stroke="#3b82f6"
            fill="#eff6ff"
            onChange={handleBrushChange}
            tickFormatter={(date) => {
              const d = new Date(date);
              return `${d.getMonth() + 1}/${d.getDate()}`;
            }}
          />
        </LineChart>
      </ResponsiveContainer>

      {brushStartIndex !== undefined && brushEndIndex !== undefined && (
        <div className="mt-4 flex items-center justify-between text-sm text-gray-600 bg-blue-50 px-4 py-2 rounded">
          <span>
            Viewing: {formatDate(data[brushStartIndex]?.date)} to{' '}
            {formatDate(data[brushEndIndex]?.date)}
          </span>
          <button
            onClick={() => {
              setBrushStartIndex(undefined);
              setBrushEndIndex(undefined);
            }}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Reset Zoom
          </button>
        </div>
      )}
    </div>
  );
}
