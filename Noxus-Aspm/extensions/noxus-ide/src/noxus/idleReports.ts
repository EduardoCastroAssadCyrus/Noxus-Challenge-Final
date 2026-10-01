// Espera global: digitar em qualquer arquivo reinicia os dez segundos.
// Os analisadores continuam sincronizados; só a publicação dos resultados espera.
export const REPORT_IDLE_MS = 10_000;

interface Clock {
  now(): number;
  schedule(callback: () => void, delay: number): unknown;
  cancel(timer: unknown): void;
}

const realClock: Clock = {
  now: () => Date.now(),
  schedule: (callback, delay) => setTimeout(callback, delay),
  cancel: timer => clearTimeout(timer as ReturnType<typeof setTimeout>)
};

export class IdleReports {
  private timer: unknown;
  private lastEdit: number;
  private disposed = false;
  private pending = new Map<string, { uri: string; publish: () => void }>();

  constructor(private readonly clock: Clock = realClock) {
    this.lastEdit = clock.now();
  }

  activity(uri: string): void {
    if (this.disposed) return;
    this.lastEdit = this.clock.now();
    // Um resultado da versão anterior não deve aparecer após a próxima edição.
    this.forget(uri);
    this.arm();
  }

  enqueue(channel: string, uri: string, publish: () => void): void {
    if (this.disposed) return;
    // Mantém apenas o resultado mais recente por arquivo e tipo de análise.
    this.pending.set(`${channel}:${uri}`, { uri, publish });
    this.arm();
  }

  forget(uri: string): void {
    for (const [key, report] of this.pending) {
      if (report.uri === uri) this.pending.delete(key);
    }
  }

  private arm(): void {
    this.clock.cancel(this.timer);
    if (!this.pending.size) return;
    const remaining = Math.max(0, REPORT_IDLE_MS - (this.clock.now() - this.lastEdit));
    this.timer = this.clock.schedule(() => {
      if (this.disposed) return;
      const reports = [...this.pending.values()];
      this.pending.clear();
      for (const report of reports) report.publish();
    }, remaining);
  }

  dispose(): void {
    this.disposed = true;
    this.clock.cancel(this.timer);
    this.pending.clear();
  }
}
