import {
  BarChart3,
  Blocks,
  Gauge,
  GitCompareArrows,
  Images,
  LayoutGrid,
  Megaphone,
  PlaySquare,
  Settings,
  ShieldCheck,
  Sparkles,
  Zap,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Build phase that wires this page up to real data; null means it's live now. */
  comingInPhase: number | null;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Overview", icon: Gauge, comingInPhase: 2 },
  { href: "/campaigns", label: "Campaigns", icon: Megaphone, comingInPhase: 2 },
  { href: "/adsets", label: "Ad Sets", icon: LayoutGrid, comingInPhase: 2 },
  { href: "/ads", label: "Ads", icon: PlaySquare, comingInPhase: 2 },
  { href: "/creatives", label: "Creatives", icon: Images, comingInPhase: 4 },
  { href: "/analytics", label: "Analytics", icon: BarChart3, comingInPhase: 5 },
  { href: "/compare", label: "Compare", icon: GitCompareArrows, comingInPhase: 5 },
  { href: "/command-center", label: "AI Command Center", icon: Sparkles, comingInPhase: 6 },
  { href: "/actions", label: "Actions", icon: Zap, comingInPhase: null },
  { href: "/rules", label: "Rules", icon: ShieldCheck, comingInPhase: null },
  { href: "/integrations", label: "Integrations", icon: Blocks, comingInPhase: 2 },
  { href: "/system", label: "System", icon: Settings, comingInPhase: null },
];
