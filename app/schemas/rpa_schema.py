from enum import Enum, IntEnum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class MeliusProcessRequest(BaseModel):
    process_data: dict


class TipoTarefaRpa(str, Enum):
    """
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


class MeliusWebhookRequest(BaseModel):
    id_tarefa_cliente: str
    tipo_tarefa_rpa: TipoTarefaRpa
    status_tarefa_rpa: StatusTarefaRpa
    arquivosGerados: list[ArquivoGerado]

    model_config = ConfigDict(
        alias_generator=to_camel,
    )
