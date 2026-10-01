import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendPoint } from "@/lib/noxus/types";

const series = [
  { key: "critical", label: "Crítico", color: "var(--critical)" },
  { key: "high", label: "Alto", color: "var(--high)" },
  { key: "medium", label: "Médio", color: "var(--medium)" },
  { key: "low", label: "Baixo", color: "var(--low)" },
  { key: "info", label: "Info", color: "var(--info)" },
  { key: "unknown", label: "Não informada", color: "var(--muted-foreground)" },
] as const;

export function TrendChart({ data }: { data: TrendPoint[] }) {
  if (!data.length)
    return (
      <p className="py-12 text-center text-sm text-muted-foreground">
        O histórico aparecerá após a primeira importação.
      </p>
    );
  const chartData = data.map((p) => ({
    ...p,
    // Evita mudança de dia causada por fuso horário ao interpretar uma data sem horário.
    label: `${p.date.slice(8, 10)}/${p.date.slice(5, 7)}`,
  }));

  return (
    <div
      className="mt-2 h-64 min-h-64 w-full flex-1"
      role="img"
      aria-label="Achados recebidos por dia e severidade"
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
          <defs>
            {series.map((s) => (
              <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={s.color} stopOpacity={0.45} />
                <stop offset="100%" stopColor={s.color} stopOpacity={0.02} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid stroke="var(--border)" vertical={false} />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
          />
          <YAxis
            allowDecimals={false}
            tickLine={false}
            axisLine={false}
            tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              background: "var(--popover)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 12,
              color: "var(--popover-foreground)",
            }}
          />
          {series.map((s) => (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.label}
              stackId="1"
              stroke={s.color}
              fill={`url(#grad-${s.key})`}
              strokeWidth={1.5}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
