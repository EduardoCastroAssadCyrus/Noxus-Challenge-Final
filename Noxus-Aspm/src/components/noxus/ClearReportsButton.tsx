import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { clearReports } from "@/lib/noxus/api";

// Temporário: remover este controle ao encerrar a fase de prototipagem.
export function ClearReportsButton() {
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function clear() {
    setBusy(true);
    setError("");
    try {
      await clearReports();
      // Descarta respostas antigas que ainda estavam chegando durante a limpeza.
      await client.cancelQueries({ queryKey: ["noxus"] });
      await client.invalidateQueries({ queryKey: ["noxus"] });
      setOpen(false);
      toast.success("Relatórios e análises removidos.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível limpar os dados.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <AlertDialog
      open={open}
      onOpenChange={(value) => {
        if (!busy) {
          setOpen(value);
          setError("");
        }
      }}
    >
      <AlertDialogTrigger asChild>
        <Button variant="destructive" size="sm">
          <Trash2 /> Limpar dados
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Limpar todos os relatórios?</AlertDialogTitle>
          <AlertDialogDescription>
            Recurso temporário de teste. Apaga os relatórios JSON recebidos, todos os achados
            (revisados ou não pela IA) e o histórico das análises. Não há como desfazer. Os
            cadastros dos ativos e do Agent são mantidos. Um Agent em monitoramento pode enviar
            novos relatórios depois da limpeza.
          </AlertDialogDescription>
        </AlertDialogHeader>
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        <AlertDialogFooter>
          <AlertDialogCancel disabled={busy}>Cancelar</AlertDialogCancel>
          <Button variant="destructive" disabled={busy} onClick={clear}>
            {busy ? "Limpando…" : "Apagar todos os relatórios"}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
