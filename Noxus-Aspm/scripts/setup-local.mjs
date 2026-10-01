import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

// Instalação local sem alterar a política de execução do PowerShell.
const project = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const backend = join(project, "backend");
const environment = join(backend, ".venv-local");
const environmentPython = join(
  environment,
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const windowsPython = join(process.env.LOCALAPPDATA ?? "", "Programs/Python/Python313/python.exe");
const python = process.argv[2] ?? (existsSync(windowsPython) ? windowsPython : "python");

if (python === "--help") {
  console.log("Uso: bun run setup:local [caminho-do-python-3.12-ou-3.13]");
  process.exit(0);
}

function run(command, args) {
  const result = spawnSync(command, args, { cwd: project, stdio: "inherit", shell: false });
  if (result.error || result.status !== 0) {
    console.error(result.error?.message ?? "O comando falhou. Confira a mensagem acima.");
    process.exit(1);
  }
}

run(python, [
  "-c",
  "import sys; assert (3,12) <= sys.version_info[:2] < (3,14), 'Use Python 3.12 ou 3.13'",
]);
// Atualiza os caminhos dos launchers quando a pasta do projeto é renomeada.
// Em um ambiente existente, preserva os pacotes já instalados.
run(python, [
  "-m",
  "venv",
  ...(existsSync(environmentPython) ? ["--without-pip"] : []),
  environment,
]);
run(environmentPython, ["-m", "pip", "install", "-e", backend + "[dev,crew]"]);
run(process.execPath, ["install", "--frozen-lockfile"]);
console.log("Preparado. Execute bun run dev:api e, em outro terminal, bun run dev.");
