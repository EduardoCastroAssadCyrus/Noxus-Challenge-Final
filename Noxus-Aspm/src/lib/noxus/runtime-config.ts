/** Os dados vêm exclusivamente da API local; não há fallback para exemplos. */
export const noxusRuntimeConfig = {
  dataSource: "api" as const,
  apiBaseUrl: (import.meta.env["VITE_NOXUS_API_URL"] ?? "http://127.0.0.1:8000/api").replace(
    /\/$/,
    "",
  ),
};
