/** EXTENSÃO NOXUS: helper do futuro fork SonarQube for IDE para VS Code.
 * NÃO pertence ao NoxusAgent Python; não é uma extensão pronta.
 * O envelope deve obedecer docs/scan-envelope.schema.json.
 * Obter apiKey via vscode.ExtensionContext.secrets, nunca hardcode.
 */
export const NOXUS_VSCODE_EXTENSION_SOURCE = "noxus-vscode-extension" as const;
export const NOXUS_VSCODE_EXTENSION_ROUTE = "/api/integrations/noxus-vscode/scans";

export async function sendNoxusExtensionScan(
  apiBaseUrl: string,
  apiKey: string,
  envelope: Record<string, unknown>,
): Promise<{ scan_id: string; received: number; replayed: boolean }> {
  if (envelope.source !== NOXUS_VSCODE_EXTENSION_SOURCE) {
    throw new Error("Envelope deve identificar a EXTENSÃO NOXUS.");
  }
  const response = await fetch(apiBaseUrl.replace(/\/$/, "") + NOXUS_VSCODE_EXTENSION_ROUTE, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
    body: JSON.stringify(envelope),
    signal: AbortSignal.timeout(15000),
    redirect: "error",
  });
  if (!response.ok) {
    // Não logar envelope/chave. O chamador trata fila, backoff e erros permanentes.
    throw new Error(`NOXUS extension ingest HTTP ${response.status}`);
  }
  return await response.json() as { scan_id: string; received: number; replayed: boolean };
}
