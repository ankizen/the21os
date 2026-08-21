const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("en-IN");

export function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

/** Meta returns ad-account budgets/spend as minor-unit strings (e.g. paise). */
export function formatMinorUnits(value: string | null): string {
  if (value === null) return "—";
  return currencyFormatter.format(Number(value) / 100);
}

export function formatNumber(value: number): string {
  return numberFormatter.format(value);
}

export function formatPercent(value: number | null, digits = 2): string {
  if (value === null) return "—";
  return `${value.toFixed(digits)}%`;
}

export function formatRatio(value: number | null, digits = 2): string {
  if (value === null) return "—";
  return `${value.toFixed(digits)}x`;
}
