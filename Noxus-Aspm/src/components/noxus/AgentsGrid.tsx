import { Bot, MessageSquare, GitMerge, Wrench, Siren } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { relativeTime } from "@/lib/noxus/ui";
import type { Agent, AgentId } from "@/lib/noxus/types";

const icons: Record<AgentId, LucideIcon> = {
  feedback: Bot,
  chatbot: MessageSquare,
  correlation: GitMerge,
  remediation: Wrench,
  emergency: Siren,
};

const statusMeta = {
  running: { label: "executando", dot: "bg-success text-success", text: "text-success" },
  idle: { label: "ocioso", dot: "bg-low text-low", text: "text-low" },
  degraded: { label: "degradado", dot: "bg-high text-high", text: "text-high" },
} as const;

export function AgentsGrid({ agents, compact = false }: { agents: Agent[]; compact?: boolean }) {
  return (
    <div
      className={
        compact
          ? "grid gap-3 sm:grid-cols-2 xl:grid-cols-5"
          : "grid gap-4 md:grid-cols-2 xl:grid-cols-3"
      }
    >
      {agents.map((agent) => {
        const Icon = icons[agent.id];
        const meta = statusMeta[agent.status];
        return (
          <article key={agent.id} className="panel flex flex-col p-4">
            <div className="flex items-start justify-between gap-3">
              <span className="flex size-8 items-center justify-center rounded-md bg-signal/10 text-signal">
                <Icon className="size-4" />
              </span>
              <span className={`flex items-center gap-2 font-mono text-[11px] ${meta.text}`}>
                <span className={`pulse-dot size-1.5 rounded-full ${meta.dot}`} />
                {meta.label}
              </span>
            </div>
            <h3 className="mt-3 text-sm font-semibold">{agent.name}</h3>
            {!compact ? <p className="mt-1 text-xs text-muted-foreground">{agent.role}</p> : null}
            <div className="mt-3 grid grid-cols-2 gap-2 border-t border-border pt-3">
              <div>
                <p className="label-mono">Hoje</p>
                <p className="font-mono text-lg">{agent.tasksToday}</p>
              </div>
              <div>
                <p className="label-mono">Vazão/h</p>
                <p className="font-mono text-lg">{agent.throughput}</p>
              </div>
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              {agent.lastAction}
              <span className="block opacity-70">{relativeTime(agent.lastActionAt)}</span>
            </p>
          </article>
        );
      })}
    </div>
  );
}
