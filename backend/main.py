from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

#importamos o modelo para validar os dados de entrada
from models import PedidoChat

#importamos as funçoes da bd e o processamento da IA
from database import configurar_bd, obter_esquema_bd, inserir_registo, consultar_registos, apagar_registo, editar_registo
from ai_agent import processar_conversa

app = FastAPI()

#permite que o frontend se ligue à api
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

configurar_bd()

@app.post("/chat")
def receber_mensagem(pedido: PedidoChat):
    #vai buscar a estrutura da bd e as mensagens
    esquema_atual = obter_esquema_bd()
    contexto_atual = [{"role": m.role, "content": m.content} for m in pedido.mensagens]
    
    # limite de tentativas para a ia resolver o pedido
    MAX_TENTATIVAS = 3
    for tentativa in range(MAX_TENTATIVAS):
        
        # envia tudo para a ia processar
        texto_resposta = processar_conversa(contexto_atual, esquema_atual)
        
        # verifica se a resposta tem os comandos para a base de dados
        if "comando" in texto_resposta and "[" in texto_resposta and (
            "inserir" in texto_resposta or "consultar" in texto_resposta or "apagar" in texto_resposta or "editar" in texto_resposta
        ):
            try:
                # extrai e limpa o json da resposta
                limpo = texto_resposta[texto_resposta.find("["):texto_resposta.rfind("]")+1]
                lista_pacotes = json.loads(limpo)
                
                if isinstance(lista_pacotes, dict):
                    lista_pacotes = [lista_pacotes]
                    
                resultados_bd = []
                
                # executa cada comando pedido pela ia
                for pacote in lista_pacotes:
                    comando = pacote.get("comando")
                    nome_tabela = pacote.get("tabela")
                    
                    if comando == "inserir":
                        dados = pacote["dados"]
                        inserir_registo(nome_tabela, dados)
                        resultados_bd.append(f"SUCESSO: Inserido na tabela {nome_tabela}.")
                        
                    elif comando == "consultar":
                        coluna = pacote.get("filtro_coluna", "")
                        valor = pacote.get("filtro_valor", "")
                        resultados = consultar_registos(nome_tabela, coluna, valor)
                        
                        if len(resultados) == 0:
                            resultados_bd.append(f"FALHA NA CONSULTA: Zero resultados com {coluna}='{valor}'. Se usaste o plural, tenta enviar um novo pacote JSON com o singular. Se já usaste o singular, então desiste e avisa o utilizador.")
                        else:
                            resultados_bd.append(f"RESULTADOS ENCONTRADOS: {resultados}")
                            
                    elif comando == "apagar":
                        coluna = pacote.get("filtro_coluna", "")
                        valor = pacote.get("filtro_valor", "")
                        linhas = apagar_registo(nome_tabela, coluna, valor)
                        
                        if linhas > 0:
                            resultados_bd.append(f"SUCESSO: Apaguei {linhas} registo(s) na tabela '{nome_tabela}' onde {coluna}='{valor}'.")
                        else:
                            resultados_bd.append(f"FALHA: Não encontrei nada para apagar com {coluna}='{valor}'.")

                    elif comando == "editar":
                        coluna = pacote.get("filtro_coluna", "")
                        valor = pacote.get("filtro_valor", "")
                        dados_novos = pacote.get("dados", {})
                        
                        linhas = editar_registo(nome_tabela, coluna, valor, dados_novos)
                        
                        if linhas > 0:
                            resultados_bd.append(f"SUCESSO: Atualizei {linhas} registo(s) na tabela '{nome_tabela}' onde {coluna}='{valor}'.")
                        else:
                            resultados_bd.append(f"FALHA: Não encontrei nada para editar com {coluna}='{valor}'.")
                
                # junta os resultados e devolve á IA para ela dar o resultado final
                texto_resultados = "\n".join(resultados_bd)
                contexto_atual.append({"role": "Assistente (Tentativa)", "content": texto_resposta})
                contexto_atual.append({"role": "Sistema (Base de Dados)", "content": texto_resultados})
                
            except Exception as e:
                print("Erro no Loop:", e)
                return {"resposta": "Teve um problema a comunicar com os sistemas."}
        else:
            #se nao for comando, envia a resposta final ao utilizador
            return {"resposta": texto_resposta}

    return {"resposta": "Nao consegui executar a açao apos varias tentativas."}