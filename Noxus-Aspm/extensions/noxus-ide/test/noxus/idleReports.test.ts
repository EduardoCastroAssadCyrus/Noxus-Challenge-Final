import { describe, expect, test } from 'bun:test';
import { IdleReports } from '../../src/noxus/idleReports';

function setup() {
  let now = 0;
  let sequence = 0;
  const timers = new Map<number, { at: number; callback: () => void }>();
  const scheduler = new IdleReports({
    now: () => now,
    schedule(callback, delay) {
      const id = ++sequence;
      timers.set(id, { at: now + delay, callback });
      return id;
    },
    cancel(timer) { timers.delete(timer as number); }
  });
  const advance = (ms: number) => {
    now += ms;
    for (const [id, timer] of timers) {
      if (timer.at <= now) { timers.delete(id); timer.callback(); }
    }
  };
  return { scheduler, advance };
}

describe('publicação após inatividade', () => {
  test('espera dez segundos e mantém somente o resultado mais recente', () => {
    const { scheduler, advance } = setup();
    const reports: number[] = [];
    scheduler.enqueue('issues', 'file:a', () => reports.push(1));
    scheduler.enqueue('issues', 'file:a', () => reports.push(2));
    advance(9999);
    expect(reports).toEqual([]);
    advance(1);
    expect(reports).toEqual([2]);
  });
  test('edição em outro arquivo reinicia a espera global', () => {
    const { scheduler, advance } = setup();
    const reports: string[] = [];
    scheduler.enqueue('issues', 'file:a', () => reports.push('a'));
    advance(9000);
    scheduler.activity('file:b');
    advance(9999);
    expect(reports).toEqual([]);
    advance(1);
    expect(reports).toEqual(['a']);
  });
  test('descarta resultados antigos, arquivos fechados e timers ao desativar', () => {
    const { scheduler, advance } = setup();
    const reports: string[] = [];
    scheduler.enqueue('issues', 'file:a', () => reports.push('antigo'));
    scheduler.activity('file:a');
    advance(10000);
    expect(reports).toEqual([]);
    scheduler.enqueue('issues', 'file:a', () => reports.push('fechado'));
    scheduler.forget('file:a');
    advance(10000);
    scheduler.enqueue('hotspots', 'file:b', () => reports.push('desativado'));
    scheduler.dispose();
    advance(10000);
    expect(reports).toEqual([]);
  });
});
