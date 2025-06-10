from enum import StrEnum


class TipoObrigacao(StrEnum):
    DAS = "DAS"
    DCTFWeb = "DCTFWeb"
    FGTS = "FGTS"


class RegimeTributario(StrEnum):
    NATIONAL_SIMPLE = "SIMPLES NACIONAL"

    @classmethod
    def get_by_name(cls, name: str):
        return getattr(cls, name.upper())
