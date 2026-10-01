import type { NoxusGateway } from "./gateway";
import type {
  AnalysisRun,
  AnalysisStatus,
  Asset,
  ChatMessage,
  DashboardData,
  Finding,
  Integration,
  ScanSummary,
} from "./types";

/**
 * Adaptador preparado para o backend real.
 *
 * Os endpoints abaixo são o molde inicial. A equipe de backend pode ajustar
 * autenticação, versionamento e validação sem espalhar `fetch` pelos componentes.
 */
export function createHttpGateway(apiBaseUrl: string): NoxusGateway {
  return {
    clearReports: () =>
      requestJson<{ findings: number; scans: number; runs: number }>(
        apiBaseUrl,
        "/v1/reports/clear",
        {
          method: "POST",
          body: JSON.stringify({ confirmation: "LIMPAR DADOS" }),
        },
      ),
    listScans: (signal) =>
      requestJson<ScanSummary[]>(apiBaseUrl, "/v1/scans", requestOptions(signal)),
    importFindings: (request) =>
      requestJson(apiBaseUrl, "/v1/imports", {
        method: "POST",
        body: JSON.stringify(request),
      }),
    startAnalysis: (findingIds) =>
      requestJson<AnalysisRun>(apiBaseUrl, "/v1/analysis/runs", {
        method: "POST",
        body: JSON.stringify({ findingIds }),
      }),
    analysisStatus: (signal) =>
      requestJson<AnalysisStatus>(apiBaseUrl, "/v1/analysis/status", requestOptions(signal)),
    analysisRuns: (signal) =>
      requestJson<AnalysisRun[]>(apiBaseUrl, "/v1/analysis/runs", requestOptions(signal)),
    getDashboard: (signal) =>
      requestJson<DashboardData>(apiBaseUrl, "/v1/dashboard", requestOptions(signal)),

    listAssets: (signal) => requestJson<Asset[]>(apiBaseUrl, "/v1/assets", requestOptions(signal)),

    createAsset: (request) =>
      requestJson<Asset>(apiBaseUrl, "/v1/assets", {
        method: "POST",
        body: JSON.stringify(request),
      }),

    updateAsset: (id, request) =>
      requestJson<Asset>(apiBaseUrl, `/v1/assets/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: JSON.stringify(request),
      }),

    listFindings: (signal) =>
      requestJson<Finding[]>(apiBaseUrl, "/v1/findings", requestOptions(signal)),

    listIntegrations: (signal) =>
      requestJson<Integration[]>(apiBaseUrl, "/v1/integrations", requestOptions(signal)),

    async getFinding(id, signal) {
      try {
        return await requestJson<Finding>(
          apiBaseUrl,
          `/v1/findings/${encodeURIComponent(id)}`,
          requestOptions(signal),
        );
      } catch (error) {
        if (error instanceof NoxusApiError && error.status === 404) return undefined;
        throw error;
      }
    },

    sendChatMessage: (request) =>
      requestJson<ChatMessage>(apiBaseUrl, "/v1/chat/messages", {
        method: "POST",
        body: JSON.stringify(request),
      }),
  };
}

class NoxusApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "NoxusApiError";
  }
}

function requestOptions(signal?: AbortSignal): RequestInit | undefined {
  return signal ? { signal } : undefined;
}

async function requestJson<T>(apiBaseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
    },
  });

  if (!response.ok) {
    const fallbackMessage = `A API Noxus respondeu com status ${response.status}.`;
    let message = fallbackMessage;

    try {
      const errorBody = (await response.json()) as {
        detail?: string | { message?: string } | { loc: (string | number)[]; msg: string }[];
      };
      message =
        typeof errorBody.detail === "string"
          ? errorBody.detail
          : Array.isArray(errorBody.detail)
            ? errorBody.detail
                .slice(0, 5)
                .map(
                  (error) =>
                    `${error.loc.filter((part) => part !== "body").join(".")}: ${error.msg}`,
                )
                .join("; ")
            : (errorBody.detail?.message ?? fallbackMessage);
    } catch {
      // Respostas sem JSON continuam usando uma mensagem segura e previsível.
    }

    throw new NoxusApiError(message, response.status);
  }

  // Quando o schema do backend for fechado, valide a resposta aqui antes de entregá-la à UI.
  return (await response.json()) as T;
}
