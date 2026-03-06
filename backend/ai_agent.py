import os
import google.generativeai as genai
from dotenv import load_dotenv

# carrega as variaveis do ficheiro .env
load_dotenv()
CHAVE_API = os.getenv("GEMINI_API_KEY")

# configura a api com a chave
genai.configure(api_key=CHAVE_API)

# define o modelo que a IA vai usar
modelo_ia = genai.GenerativeModel('gemini-2.0-flash')

def processar_conversa(historico_com_sistema, esquema_atual):
    # transforma o historico de mensagens numa string
    historico_texto = ""
    for msg in historico_com_sistema:
        quem = msg["role"]
        historico_texto += f"{quem}: {msg['content']}\n"
    
    # define as instruçoes e regras para a ia seguir
    instrucoes_ia = f"""
    És um Agente de IA autonomo. O teu trabalho é interagir com a base de dados da empresa para ajudar o utilizador.
    Esquema da Base de Dados: {esquema_atual}
    
    Histórico da conversa e resultados da BD:
    {historico_texto}
    
    REGRAS DE FUNCIONAMENTO:
    1. Tens acesso a 4 ferramentas: INSERIR, CONSULTAR, APAGAR e EDITAR apenas.
    2. REGRA DE SEGURANÇA: Antes de atuares, se o utilizador não disser explicitamente o nome da tabela (ex: alunos ou produtos), PERGUNTA-LHE primeiro.
    3. REGRA DE MODIFICAÇÃO: Para APAGAR ou EDITAR algo, exige SEMPRE confirmação final do utilizador antes de enviares o comando.
    4. Quando tiveres os dados todos, responde APENAS com a LISTA JSON (começa com "[" e acaba com "]").
    5. REGRA DE DESISTÊNCIA E TENTATIVAS: Se a BD devolver "FALHA NA CONSULTA", tens permissão para fazer UMA (e apenas uma) nova tentativa corrigindo a palavra para o SINGULAR se tiver no plural. Se tiver no SINGULAR corrige para PLURAL . Se falhar novamente, ACEITA A DERROTA e avisa o utilizador.
    
    FORMATOS DO JSON (Usa a ferramenta certa):
    - INSERIR: {{"comando": "inserir", "tabela": "nome", "dados": {{"coluna": "valor"}}}}
    - CONSULTAR: {{"comando": "consultar", "tabela": "nome", "filtro_coluna": "coluna", "filtro_valor": "valor"}}
    - APAGAR: {{"comando": "apagar", "tabela": "nome", "filtro_coluna": "coluna", "filtro_valor": "valor"}}
    - EDITAR: {{"comando": "editar", "tabela": "nome", "filtro_coluna": "coluna_pesquisa", "filtro_valor": "valor_pesquisa", "dados": {{"coluna_a_mudar": "novo_valor"}}}}
    """
    
    # gera a resposta da ia com base nas instruçoes
    resposta_ia = modelo_ia.generate_content(instrucoes_ia)
    
    # devolve apenas o texto da resposta
    return resposta_ia.text