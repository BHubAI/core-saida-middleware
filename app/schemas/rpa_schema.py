from pydantic import BaseModel


class MeliusProcessRequest(BaseModel):
    process_data: dict
