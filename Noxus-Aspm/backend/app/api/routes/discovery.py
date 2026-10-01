from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/asset-discovery", tags=["asset-discovery"])


@router.post("/runs")
def start_discovery_run() -> None:
    # Contrato reservado para um worker futuro. Não devolvemos candidatos
    # inventados pela API enquanto scanners/CrewAI não estiverem configurados.
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "asset_discovery_not_configured",
            "message": "A descoberta automática ainda não possui conectores configurados.",
        },
    )
