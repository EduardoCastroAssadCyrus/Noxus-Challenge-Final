import { Link } from "@tanstack/react-router";
import { Activity, Menu, ShieldCheck } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { navigationGroups } from "@/config/navigation";

function Brand() {
  return (
    <Link to="/" className="flex items-center gap-2.5">
      <span className="flex size-9 items-center justify-center rounded-md bg-signal/15 text-signal">
        <ShieldCheck className="size-5" />
      </span>
      <span>
        <span className="block text-sm font-semibold tracking-tight">Noxus</span>
        <span className="label-mono block">ASPM</span>
      </span>
    </Link>
  );
}

function Navigation({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav aria-label="Navegação principal" className="flex flex-col gap-5">
      {navigationGroups.map((group) => (
        <div key={group.label}>
          <p className="label-mono mb-1.5 px-3">{group.label}</p>
          <div className="flex flex-col gap-1">
            {group.items.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                onClick={onNavigate}
                className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                activeOptions={{ exact: item.to === "/" }}
                activeProps={{
                  className:
                    "bg-signal/10 text-signal font-medium hover:bg-signal/15 hover:text-signal",
                }}
              >
                <item.icon className="size-4" />
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      ))}
    </nav>
  );
}

function TopBar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-[1500px] items-center justify-between px-4 lg:px-6">
        <div className="lg:hidden">
          <Brand />
        </div>

        <div className="hidden items-center gap-2 lg:flex">
          <Activity className="size-4 text-signal" />
          <span className="text-sm text-muted-foreground">Console de postura de segurança</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden rounded-full border border-border px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider sm:inline-flex">
            Ambiente local
          </span>

          <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
            <SheetTrigger asChild>
              <Button className="lg:hidden" size="icon" variant="ghost" aria-label="Abrir menu">
                <Menu className="size-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-[300px] border-border bg-surface p-5">
              <SheetTitle className="sr-only">Menu principal</SheetTitle>
              <Brand />
              <div className="mt-8">
                <Navigation onNavigate={() => setMenuOpen(false)} />
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}

export function AppShell({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="grid-canvas min-h-screen bg-background">
      <TopBar />
      <div className="mx-auto flex w-full max-w-[1500px] gap-0 lg:gap-6 lg:px-6">
        <aside className="sticky top-14 hidden h-[calc(100vh-3.5rem)] w-60 shrink-0 flex-col border-r border-border py-6 pr-5 lg:flex">
          <Brand />
          <div className="mt-8">
            <Navigation />
          </div>

          <div className="panel mt-auto p-3">
            <p className="label-mono">Fase atual</p>
            <p className="mt-2 text-sm font-medium">Fluxo local</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Relatórios e análises armazenados em arquivos JSON.
            </p>
          </div>
        </aside>

        <main className="min-w-0 flex-1 px-4 py-6 lg:px-0 lg:py-8">
          <header className="mb-7 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="label-mono flex items-center gap-2">
                <Activity className="size-3.5" /> Console de segurança
              </p>
              <h1 className="mt-1.5 text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
              {subtitle ? (
                <p className="mt-1.5 max-w-3xl text-sm text-muted-foreground">{subtitle}</p>
              ) : null}
            </div>
            {actions}
          </header>

          {children}
        </main>
      </div>
    </div>
  );
}
