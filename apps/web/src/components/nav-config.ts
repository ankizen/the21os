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
  { href: "/", label: "Overview", icon: Gauge, comingInPhase: null },
  { href: "/campaigns", label: "Campaigns", icon: Megaphone, comingInPhase: null },
  { href: "/adsets", label: "Ad Sets", icon: LayoutGrid, comingInPhase: null },
  { href: "/ads", label: "Ads", icon: PlaySquare, comingInPhase: null },
  { href: "/creatives", label: "Creatives", icon: Images, comingInPhase: null },
  { href: "/analytics", label: "Analytics", icon: BarChart3, comingInPhase: null },
  { href: "/compare", label: "Compare", icon: GitCompareArrows, comingInPhase: null },
  { href: "/command-center", label: "AI Command Center", icon: Sparkles, comingInPhase: 6 },
  { href: "/actions", label: "Actions", icon: Zap, comingInPhase: null },
  { href: "/rules", label: "Rules", icon: ShieldCheck, comingInPhase: null },
  { href: "/integrations", label: "Integrations", icon: Blocks, comingInPhase: null },
  { href: "/system", label: "System", icon: Settings, comingInPhase: null },
];
