from fastapi import UploadFile

from app.api.base.endpoints import BaseEndpoint
from app.api.deps import DBSession, DDLogger
from app.schemas.audit_schema import CalculoDesvioRequest
from app.service.audit.obrigacoes_acessorias import (
    calcula_desvio_obrigacao,
    import_desvio_from_file,
)


ROUTE_PREFIX = "/api/obrigacoes"


class ObrigacoesAcessoriasEndpoint(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["Obrigacoes Acessorias"], prefix=ROUTE_PREFIX)

        @self.router.post("/import-desvio")
        def _import_desvio(file: UploadFile, db_session: DBSession, logger: DDLogger):
            try:
                logger.info(f"Importing desvio from file {file.filename}")
                if not file.filename:
                    raise ValueError("Missing file or filename")

                if not file.filename.endswith((".csv")):
                    raise ValueError("File must be .txt or .csv")

                import_desvio_from_file(file, db_session)

                logger.info("File content loaded successfully")

            except Exception as e:
                logger.error(f"Error importing desvio: {e}")
                raise e

        @self.router.post("/calculo-desvio")
        def _get_desvio(request: CalculoDesvioRequest, db_session: DBSession):
            desvio = calcula_desvio_obrigacao(request.cnpj, request.tipo_obrigacao, request.current_value, db_session)

            def label_desvio(desvio):
                if 2 <= desvio < 3.5:
                    return "MEDIUM"
                elif desvio >= 3.5:
                    return "HIGH"
                else:
                    return "OK"

            return {
                "cnpj": request.cnpj,
                "current_value": request.current_value,
                "tipo_obrigacao": request.tipo_obrigacao,
                "desvio": desvio,
                "label_desvio": label_desvio(desvio),
            }
