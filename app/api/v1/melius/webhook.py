from enum import IntEnum, StrEnum
from typing import Any
import httpx
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from api.base.endpoints import BaseEndpoint


class TipoTarefaRpa(StrEnum):
    """ "
    Tipos de tarefa RPA

    DCTFWeb + FGTS	Enviar eSocial	envEsocial
    DCTFWeb + FGTS	Enviar Reinf	envReinf
    DCTFWeb + FGTS	Gerar DARF DCTFWeb	gerDarfDct
    DCTFWeb + FGTS	Gerar DARF MIT	gerDarfMit
    DCTFWeb + FGTS	Gerar Guia FGTS	gerFgts
    DCTFWeb + FGTS	Transmitir MIT	traMit
    DCTFWeb + FGTS	Transmitir DCTFWeb	traDctf
    SPED	Transmitir EFD Contribuições	efdContrib
    SPED	Transmitir EFD IPI/ICMS	efdIpiIcms
    SPED	Transmitir Contribuições Sem Movimento	contrSeMv
    DeSTDA	Transmitir DeSTDA	traDestda
    DeSTDA	Transmitir DeSTDA Sem Movimento	traSeMv
    """

    ENVIAR_ESOCIAL = "envEsocial"
    ENVIAR_REINF = "envReinf"
    GERAR_DARF_DCT = "gerDarfDct"
    GERAR_DARF_MIT = "gerDarfMit"
    GERAR_GUIA_FGTS = "gerFgts"
    TRANSMITIR_MIT = "traMit"
    TRANSMITIR_DCTFWEB = "traDctf"
    TRANSMITIR_EFD_CONTRIBUICOES = "efdContrib"
    TRANSMITIR_EFD_IPI_ICMS = "efdIpiIcms"
    TRANSMITIR_CONTRIBUICOES_SEM_MOVIMENTO = "contrSeMv"
    TRANSMITIR_DESTDA = "traDestda"
    TRANSMITIR_DESTDA_SEM_MOVIMENTO = "traSeMv"


class StatusTarefaRpa(IntEnum):
    """
    Status da tarefa RPA
    """

    CONCLUIDA_COM_SUCESSO = 1
    TRATATIVA_MANUAL = 2


class ArquivoGerado(BaseModel):
    url: str
    nome_arquivo: str

    model_config = ConfigDict(
        alias_generator=to_camel,
    )


class WebhookRequest(BaseModel):
    id_tarefa_cliente: str
    tipo_tarefa_rpa: TipoTarefaRpa
    status_tarefa_rpa: StatusTarefaRpa
    arquivosGerados: list[ArquivoGerado]

    model_config = ConfigDict(
        alias_generator=to_camel,
    )


class CamundaRequest(BaseModel):
    message_name: str
    process_variables: dict[str, dict[str, Any]]
    process_instance_id: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
    )


class MeliusWebhookEndpoint(BaseEndpoint):
    """Melius Webhook endpoint"""

    def __init__(self):
        super().__init__(tags=["Webhook"], prefix="/api/melius")

        @self.router.post("/webhook")
        async def melius_webhook(request: WebhookRequest):
            """
            Webhook para receber update dos RPAs da Melius.

            - Recebe o payload do webhook
            - Processa o payload
            - Envia o payload para o Camunda
            """

            camunda_request = CamundaRequest(
                message_name=f"retorno:{request.tipo_tarefa_rpa}",
                process_variables={
                    "statusTarefaRpa": {
                        "value": request.status_tarefa_rpa,
                        "type": "integer",
                    },
                    "arquivosGerados": {
                        "value": [
                            {
                                "url": arquivo.url,
                                "nomeArquivo": arquivo.nome_arquivo,
                            }
                            for arquivo in request.arquivosGerados
                        ],
                    },
                },
                process_instance_id=request.id_tarefa_cliente,
            )

            httpx.post(
                "http://localhost:8080/engine-rest/message",
                json=camunda_request.model_dump(by_alias=True),
            )

            return {"message": "Melius webhook received"}
