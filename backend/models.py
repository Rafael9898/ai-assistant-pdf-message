from pydantic import BaseModel
from typing import List

# define a estrutura de uma unica mensagem
class Mensagem(BaseModel):
    role: str
    content: str

# define a lista de mensagens que vem do front
class PedidoChat(BaseModel):
    mensagens: List[Mensagem]