export interface NavItem {
  href: string;
  label: string;
  /** Build phase that wires this page up to real data; null means it's live now. */
  comingInPhase: number | null;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Overview", comingInPhase: 2 },
  { href: "/campaigns", label: "Campaigns", comingInPhase: 2 },
  { href: "/adsets", label: "Ad Sets", comingInPhase: 2 },
  { href: "/ads", label: "Ads", comingInPhase: 2 },
  { href: "/creatives", label: "Creatives", comingInPhase: 4 },
  { href: "/analytics", label: "Analytics", comingInPhase: 5 },
  { href: "/compare", label: "Compare", comingInPhase: 5 },
  { href: "/command-center", label: "AI Command Center", comingInPhase: 6 },
  { href: "/actions", label: "Actions", comingInPhase: null },
  { href: "/rules", label: "Rules", comingInPhase: null },
  { href: "/integrations", label: "Integrations", comingInPhase: 2 },
  { href: "/system", label: "System", comingInPhase: null },
];
