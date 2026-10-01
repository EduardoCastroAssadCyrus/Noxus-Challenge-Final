import type { FindingStatus, Severity } from "./types";

export const analysisLabel = {
  true_positive: "Provável verdadeiro positivo",
  false_positive: "Possível falso positivo",
  inconclusive: "Inconclusivo",
};

export const severityLabel: Record<Severity, string> = {
  critical: "Crítico",
  high: "Alto",
  medium: "Médio",
  low: "Baixo",
  info: "Info",
};

export const severityClass: Record<Severity, string> = {
  critical: "bg-critical/15 text-critical border-critical/30",
  high: "bg-high/15 text-high border-high/30",
  medium: "bg-medium/15 text-medium border-medium/30",
  low: "bg-low/15 text-low border-low/30",
  info: "bg-info/15 text-info border-info/30",
};

export const severityBar: Record<Severity, string> = {
  critical: "bg-critical",
  high: "bg-high",
  medium: "bg-medium",
  low: "bg-low",
  info: "bg-info",
};

export const statusLabel: Record<FindingStatus, string> = {
  open: "Aberto",
  triaged: "Triado",
  needs_review: "Revisão humana",
  in_progress: "Em correção",
  resolved: "Resolvido",
  false_positive: "Falso positivo",
};

export const statusClass: Record<FindingStatus, string> = {
  open: "bg-critical/10 text-critical",
  triaged: "bg-medium/10 text-medium",
  needs_review: "bg-signal/10 text-signal",
  in_progress: "bg-low/10 text-low",
  resolved: "bg-success/10 text-success",
  false_positive: "bg-muted text-muted-foreground",
};

export function relativeTime(iso: string, reference = Date.now()): string {
  const diff = Math.max(0, reference - new Date(iso).getTime());
  const minutes = Math.round(diff / 60_000);
  if (minutes < 1) return "agora";
  if (minutes < 60) return `há ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `há ${hours} h`;
  return `há ${Math.round(hours / 24)} d`;
}
