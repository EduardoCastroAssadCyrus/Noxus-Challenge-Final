import { Bot, Boxes, LayoutDashboard, MessageSquare, PlugZap, ShieldAlert } from "lucide-react";

/** Menu único usado no desktop e no mobile para evitar rotas duplicadas. */
export const navigationGroups = [
  {
    label: "Visão geral",
    items: [{ to: "/", label: "Cérebro Central", icon: LayoutDashboard }],
  },
  {
    label: "Postura",
    items: [
      { to: "/assets", label: "Aplicações e ativos", icon: Boxes },
      { to: "/findings", label: "Vulnerabilidades", icon: ShieldAlert },
    ],
  },
  {
    label: "Operação",
    items: [
      { to: "/integrations", label: "Integrações", icon: PlugZap },
      { to: "/agents", label: "Equipe Agêntica", icon: Bot },
    ],
  },
  {
    label: "Assistente",
    items: [{ to: "/chat", label: "Chatbot de Risco", icon: MessageSquare }],
  },
] as const;
