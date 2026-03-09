from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import pandas as pd
import io
from typing import Optional

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
async def receber_mensagem(
    mensagens_json: str = Form(...),
    ficheiro: Optional[UploadFile] = File(None) ):

    #vai buscar a estrutura da bd e as mensagens
    esquema_atual = obter_esquema_bd()

    # converte as mensagens recebidas para uma lista que o python saiba ler
    mensagens_lista = json.loads(mensagens_json)
    contexto_atual = [{"role": m["role"], "content": m["content"]} for m in mensagens_lista]

    
    info_ficheiro = None
    dados_ficheiro = None

    ## se o utilizador enviou um ficheiro, vamos le-lo
    if ficheiro:
        conteudo = await ficheiro.read()
        nome = ficheiro.filename.lower()

        # verifica se é csv ou excel
        if nome.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(conteudo))
        elif nome.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(conteudo))
        else:
            return {"resposta": "Formato de ficheiro não suportado. Use .xlsx ou .csv."}

        # tenta transformar tudo o que parece um numero para numero real
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass
        
        #prepara uma amostra dos dados para a IA ver
        colunas_ficheiro = list(df.columns)
        num_linhas = len(df)
        amostra = df.head(3).to_dict(orient="records")
        dados_ficheiro = df.to_dict(orient="records")

        #guarda o ficheiro todo num ficheiro temporario local
        with open("_dados_ficheiro_temp.json", "w", encoding="utf-8") as f:
            json.dump(dados_ficheiro, f, ensure_ascii=False, default=str)

        # cria o resumo para avisar a IA do que recebemos
        info_ficheiro = (
            f"O utilizador enviou o ficheiro '{ficheiro.filename}' com {num_linhas} linhas. "
            f"Colunas: {colunas_ficheiro}. "
            f"Amostra das primeiras 3 linhas: {amostra}. "
            f"Diz ao utilizador em que tabela quer inserir e confirma se as colunas tao certas compaarada com o esquema da BD."
        )
        contexto_atual.append({"role": "Sistema (Ficheiro)", "content": info_ficheiro})
    
    # limite de tentativas para a IA resolver o pedido
    MAX_TENTATIVAS = 3
    for tentativa in range(MAX_TENTATIVAS):
        
        # envia tudo para a IA processar
        texto_resposta = processar_conversa(contexto_atual, esquema_atual)
        
        # verifica se a resposta tem os comandos para a base de dados
        if "comando" in texto_resposta and "[" in texto_resposta and (
            "inserir" in texto_resposta or "consultar" in texto_resposta or "apagar" in texto_resposta or "editar" in texto_resposta or "inserir_ficheiro" in texto_resposta
        ):
            try:
                # extrai e limpa o json da resposta
                limpo = texto_resposta[texto_resposta.find("["):texto_resposta.rfind("]")+1]
                lista_pacotes = json.loads(limpo)
                
                if isinstance(lista_pacotes, dict):
                    lista_pacotes = [lista_pacotes]
                    
                resultados_bd = []
                
                # executa cada comando pedido pela IA
                for pacote in lista_pacotes:
                    comando = pacote.get("comando")
                    nome_tabela = pacote.get("tabela")
                    
                    if comando == "inserir_ficheiro":
                        # se não tem dados em memoria, tenta carregar do temporário
                        if not dados_ficheiro and os.path.exists("_dados_ficheiro_temp.json"):
                            with open("_dados_ficheiro_temp.json", "r", encoding="utf-8") as f:
                                dados_ficheiro = json.load(f)
                            os.remove("_dados_ficheiro_temp.json")

                        # insere os dados do ficheiro linha por linha
                        if dados_ficheiro:
                            mapeamento = pacote.get("mapeamento", {})
                            total = 0
                            for linha in dados_ficheiro:
                                # se a IA pediu para trocar o nome de alguma coluna antes de gravar
                                if mapeamento:
                                    novo = {}
                                    for col_bd, col_fich in mapeamento.items():
                                        novo[col_bd] = linha.get(col_fich, "")
                                    inserir_registo(nome_tabela, novo)
                                else:
                                    # senao grava os dados diretos
                                    inserir_registo(nome_tabela, linha)
                                total += 1
                            resultados_bd.append(f"SUCESSO: Inseridos {total} registos na tabela '{nome_tabela}' (um a um).")
                        else:
                            resultados_bd.append("FALHA: Não há dados de ficheiro para inserir.")

                    elif comando == "inserir":
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
                
                # junta os resultados para a ia ler
                texto_resultados = "\n".join(resultados_bd)
                contexto_atual.append({"role": "Assistente (Tentativa)", "content": texto_resposta})
                contexto_atual.append({"role": "Sistema (Base de Dados)", "content": texto_resultados})
                
            except Exception as e:
                print("Erro no Loop:", e)
                
                # se algo der erro, devolve o erro para a IA para ela tentar corrigir
                contexto_atual.append({"role": "Sistema (Base de Dados)", "content": f"ERRO TÉCNICO: {e}. Corrige o comando e tenta novamente."})
        else:
            #se nao for comando, envia a resposta final ao utilizador
            return {"resposta": texto_resposta}

    return {"resposta": "Nao consegui executar a açao apos varias tentativas."}