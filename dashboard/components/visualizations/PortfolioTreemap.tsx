'use client';

import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

interface TreemapData {
  name: string;
  size: number;
  value?: number;
  sector?: string;
  id?: string;
}

interface PortfolioTreemapProps {
  data: TreemapData[];
  title?: string;
}

const COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#14b8a6', // teal
  '#f97316', // orange
  '#6366f1', // indigo
  '#84cc16', // lime
];

export function PortfolioTreemap({ data, title }: PortfolioTreemapProps) {
  // Ensure data has unique keys
  const uniqueData = data.map((item, index) => ({
    ...item,
    id: item.id || `${item.name}-${index}-${item.size}`,
  }));

  // Create a lookup map for portfolio weights by name
  const weightMap = new Map(data.map(item => [item.name, item.value || 0]));

  const CustomizedContent = (props: any) => {
    const { x, y, width, height, index, name } = props;

    if (width < 50 || height < 30) {
      return null; // Don't render if too small
    }

    // Look up the portfolio weight from our map
    const portfolioWeight = weightMap.get(name) || 0;
    const percentage = (portfolioWeight * 100).toFixed(1);

    return (
      <g>
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          style={{
            fill: COLORS[index % COLORS.length],
            stroke: '#fff',
            strokeWidth: 2,
            opacity: 0.9,
          }}
        />
        <text
          x={x + width / 2}
          y={y + height / 2 - 8}
          textAnchor="middle"
          fill="#fff"
          fontSize={width > 100 ? 14 : 11}
          fontWeight="bold"
        >
          {name}
        </text>
        <text
          x={x + width / 2}
          y={y + height / 2 + 10}
          textAnchor="middle"
          fill="#fff"
          fontSize={width > 100 ? 12 : 10}
        >
          {percentage}%
        </text>
      </g>
    );
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const portfolioWeight = weightMap.get(data.name) || 0;
      return (
        <div className="bg-white dark:bg-gray-800 px-4 py-2 border border-gray-200 dark:border-gray-600 rounded shadow-lg">
          <p className="font-semibold text-gray-900 dark:text-white">{data.name}</p>
          {data.sector && (
            <p className="text-sm text-gray-600 dark:text-gray-400">Sector: {data.sector}</p>
          )}
          <p className="text-sm text-gray-600 dark:text-gray-400">
            ${data.size?.toLocaleString()} ({(portfolioWeight * 100).toFixed(2)}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={400}>
        <Treemap
          data={uniqueData}
          dataKey="size"
          nameKey="id"
          aspectRatio={4 / 3}
          stroke="#fff"
          fill="#8884d8"
          content={<CustomizedContent />}
        >
          <Tooltip content={<CustomTooltip />} />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
}
