from enum import IntEnum
from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class MeliusProcessRequest(BaseModel):
    process_data: dict


class StatusTarefaRpa(IntEnum):
    """
    Status da tarefa RPA
    """

    CONCLUIDA_COM_SUCESSO = 1
    TRATATIVA_MANUAL = 2


class ArquivoGerado(BaseModel):
    """
    Arquivo gerado pelo RPA
    """

    url: str
    nome_arquivo: str
    tipo_arquivo: str

    model_config = ConfigDict(
        alias_generator=to_camel,
    )


class MeliusParametrosComplementares(BaseModel):
    sem_movimento: bool = False

    model_config = ConfigDict(
        alias_generator=to_camel,
    )


class MeliusWebhookRequest(BaseModel):
    id_tarefa_cliente: str
    status_tarefa_rpa: StatusTarefaRpa
    mensagem_retorno: str | None = None
    arquivos_gerados: list[ArquivoGerado] | None = None
    token_retorno: str
    parametros_complementares: MeliusParametrosComplementares | None = None

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
