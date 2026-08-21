const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 31536000],
  ["month", 2592000],
  ["day", 86400],
  ["hour", 3600],
  ["minute", 60],
];

const formatter = new Intl.RelativeTimeFormat("en", { numeric: "always", style: "short" });

export function relativeTime(iso: string): string {
  const seconds = (Date.now() - new Date(iso).getTime()) / 1000;
  if (seconds < 60) return "just now";
  for (const [unit, secondsInUnit] of UNITS) {
    if (seconds >= secondsInUnit) {
      return formatter.format(-Math.floor(seconds / secondsInUnit), unit);
    }
  }
  return formatter.format(-Math.floor(seconds / 60), "minute");
}
