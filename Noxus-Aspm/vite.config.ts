import tailwindcss from "@tailwindcss/vite";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import viteReact from "@vitejs/plugin-react";
import { nitro } from "nitro/vite";
import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 3000,
  },
  resolve: {
    tsconfigPaths: true,
  },
  plugins: [
    tanstackStart({
      // Mantém src/server.ts como ponto futuro de autenticação, logs e contexto do backend.
      server: { entry: "server" },
    }),
    nitro(),
    // O plugin React precisa vir depois do plugin do TanStack Start.
    viteReact(),
    tailwindcss(),
  ],
});
