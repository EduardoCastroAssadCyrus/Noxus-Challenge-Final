import { Database } from "lucide-react";
import { cn } from "@/lib/utils";

export function DemoNotice({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "mb-5 flex items-center gap-2 rounded-md border border-border p-3 text-xs text-muted-foreground",
        className,
      )}
    >
      <Database className="size-4" /> Ambiente local · dados importados e análises armazenados em
      JSON.
    </div>
  );
}
