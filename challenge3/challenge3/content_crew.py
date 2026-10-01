"""API Python do fluxo local. O dashboard usa noxus_bridge.py em subprocesso."""

from pathlib import Path

from noxus_bridge import analyze


class VulnerabilityFilterCrew:
    def run(self, input_file: Path, output_file: Path, progress_file: Path):
        # Os quatro papéis continuam definidos em config/agents.yaml.
        # A execução direta de Task evita a persistência SQLite de Crew.kickoff.
        return analyze(Path(__file__).resolve().parent, input_file, output_file, progress_file)
