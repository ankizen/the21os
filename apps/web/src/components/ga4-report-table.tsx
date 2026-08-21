import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/empty-state";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { Ga4Report } from "@/lib/types";

const CURRENCY_METRICS = new Set(["totalRevenue", "purchaseRevenue"]);

function formatMetric(key: string, value: number): string {
  return CURRENCY_METRICS.has(key) ? formatCurrency(value) : formatNumber(value);
}

export function Ga4ReportTable({ report }: { report: Ga4Report | undefined }) {
  if (!report || report.rows.length === 0) {
    return <EmptyState title="No data" description="No sessions in this date range." />;
  }

  const dimensionKeys = Object.keys(report.rows[0].dimensions);
  const metricKeys = Object.keys(report.rows[0].metrics);

  return (
    <div className="overflow-hidden rounded-lg border">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              {dimensionKeys.map((k) => (
                <TableHead key={k}>{k}</TableHead>
              ))}
              {metricKeys.map((k) => (
                <TableHead key={k} className="text-right">
                  {k}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.rows.map((row, i) => (
              // Rows have no stable id from the API — fine for a static, read-only report table.
              <TableRow key={i}>
                {dimensionKeys.map((k) => (
                  <TableCell key={k} className="max-w-64 truncate text-sm">
                    {row.dimensions[k] || "—"}
                  </TableCell>
                ))}
                {metricKeys.map((k) => (
                  <TableCell key={k} className="text-right text-sm">
                    {formatMetric(k, row.metrics[k] ?? 0)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
