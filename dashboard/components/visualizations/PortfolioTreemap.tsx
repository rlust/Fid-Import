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

  const CustomizedContent = (props: any) => {
    const { x, y, width, height, index, name, size, value } = props;

    if (width < 50 || height < 30) {
      return null; // Don't render if too small
    }

    const percentage = value ? (value * 100).toFixed(1) : '0.0';

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
      return (
        <div className="bg-white px-4 py-2 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold text-gray-900">{data.name}</p>
          {data.sector && (
            <p className="text-sm text-gray-600">Sector: {data.sector}</p>
          )}
          <p className="text-sm text-gray-600">
            ${data.size?.toLocaleString()} ({(data.value * 100).toFixed(2)}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
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
