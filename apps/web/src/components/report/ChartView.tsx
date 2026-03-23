import React from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

interface ChartViewProps {
  graphData: any; // Can be JSON from backend describing chart type, labels, values
}

export default function ChartView({ graphData }: ChartViewProps) {
  if (!graphData) return null;

  // Determine chart type
  const { type, data, xKey, yKey, name } = graphData;

  return (
    <div className="my-4 p-2 border rounded shadow-sm bg-white">
      <h3 className="font-semibold mb-2">{name || "Graph"}</h3>
      <ResponsiveContainer width="100%" height={300}>
        {type === "line" ? (
          <LineChart data={data}>
            <CartesianGrid stroke="#eee" strokeDasharray="5 5" />
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={yKey} stroke="#8884d8" />
          </LineChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid stroke="#eee" strokeDasharray="5 5" />
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={yKey} fill="#82ca9d" />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}