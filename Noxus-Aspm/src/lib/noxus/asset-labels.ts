import type {
  AssetAccess,
  AssetDataClassification,
  AssetHosting,
  AssetRegistrationSource,
  AssetRegistryStatus,
  AssetType,
  EnvironmentType,
  Severity,
} from "./types";

export const environmentLabel = {
  unknown: "Ambiente não informado",
  production: "Produção",
  staging: "Homologação",
  test: "Teste",
  development: "Desenvolvimento",
  shared: "Multiambiente",
} satisfies Record<EnvironmentType, string>;

export const assetTypeLabel = {
  application: "Aplicação",
  repository: "Repositório",
  api: "API",
  service: "Serviço",
  database: "Banco de dados",
  container: "Container",
} satisfies Record<AssetType, string>;

export const assetAccessLabel = {
  unknown: "Acesso não informado",
  public_internet: "Internet pública",
  restricted_internet: "Internet com autenticação",
  private_network: "Rede privada",
} satisfies Record<AssetAccess, string>;

export const assetHostingLabel = {
  unknown: "Hospedagem não informada",
  saas: "SaaS",
  public_cloud: "Nuvem pública",
  private_cloud: "Nuvem privada",
  on_premises: "Datacenter próprio",
} satisfies Record<AssetHosting, string>;

export const assetDataLabel = {
  unknown: "Classificação não informada",
  public: "Pública",
  internal: "Interna",
  confidential: "Confidencial",
  restricted: "Restrita",
} satisfies Record<AssetDataClassification, string>;

export const assetSourceLabel = {
  manual: "Adicionado manualmente",
  ai_discovery: "Encontrado automaticamente",
  integration: "Encontrado automaticamente",
} satisfies Record<AssetRegistrationSource, string>;

export const assetStatusLabel = {
  active: "Ativo",
  pending_review: "Revisão pendente",
  inactive: "Inativo",
} satisfies Record<AssetRegistryStatus, string>;

export const severityLabel = {
  critical: "Crítica",
  high: "Alta",
  medium: "Média",
  low: "Baixa",
  info: "Informativa",
} satisfies Record<Severity, string>;
