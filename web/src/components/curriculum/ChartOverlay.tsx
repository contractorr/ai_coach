"use client";

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { ParsedChartData } from "@/lib/chart-parser";

const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

interface Props {
  data: ParsedChartData;
}

export function ChartOverlay({ data }: Props) {
  const { chartType, xLabel, yLabel, series } = data;

  const axisProps = {
    tick: { fontSize: 11, className: "fill-muted-foreground" },
    tickLine: false,
    axisLine: false,
  };

  if (chartType === "bar") {
    return (
      <ResponsiveContainer width="100%" height={256}>
        <BarChart data={data.data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis dataKey={xLabel} {...axisProps} />
          <YAxis label={yLabel ? { value: yLabel, angle: -90, position: "insideLeft", fontSize: 11 } : undefined} {...axisProps} />
          <Tooltip contentStyle={{ fontSize: 12 }} />
          {series.length > 1 && <Legend wrapperStyle={{ fontSize: 11 }} />}
          {series.map((key, i) => (
            <Bar key={key} dataKey={key} fill={CHART_COLORS[i % CHART_COLORS.length]} radius={[2, 2, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "scatter") {
    return (
      <ResponsiveContainer width="100%" height={256}>
        <ScatterChart margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis dataKey="x" name={xLabel} {...axisProps} />
          <YAxis dataKey="y" name={yLabel || "y"} {...axisProps} />
          <Tooltip contentStyle={{ fontSize: 12 }} />
          <Scatter data={data.data} fill={CHART_COLORS[0]} />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  // Default: line chart
  return (
    <ResponsiveContainer width="100%" height={256}>
      <LineChart data={data.data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey={xLabel} {...axisProps} />
        <YAxis label={yLabel ? { value: yLabel, angle: -90, position: "insideLeft", fontSize: 11 } : undefined} {...axisProps} />
        <Tooltip contentStyle={{ fontSize: 12 }} />
        {series.length > 1 && <Legend wrapperStyle={{ fontSize: 11 }} />}
        {series.map((key, i) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={CHART_COLORS[i % CHART_COLORS.length]}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
