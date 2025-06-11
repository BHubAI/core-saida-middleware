from pydantic import BaseModel


class CalculoDesvioRequest(BaseModel):
    cnpj: str
    tipo_obrigacao: str
    current_value: float
