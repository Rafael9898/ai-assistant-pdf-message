import os
from google import genai
from dotenv import load_dotenv

# carrega as variaveis do ficheiro .env
load_dotenv()
CHAVE_API = os.getenv("GEMINI_API_KEY")

# Inicializa o novo cliente oficial da Google
cliente = genai.Client(api_key=CHAVE_API)

def processar_conversa(historico_com_sistema, esquema_atual):
    # transforma o historico de mensagens numa string
    historico_texto = ""
    for msg in historico_com_sistema:
        quem = msg["role"]
        historico_texto += f"{quem}: {msg['content']}\n"
    
    # define as instruçoes e regras para a IA
    instrucoes_ia = f"""
    És um Agente de IA autonomo. O teu trabalho é interagir com a base de dados da empresa para ajudar o utilizador.
    
    Esquema da Base de Dados:
    {esquema_atual}
    
    Histórico da conversa e resultados da BD:
    {historico_texto}
    
    REGRAS DE FUNCIONAMENTO:
    1. Tens acesso a 5 ferramentas: INSERIR, CONSULTAR, APAGAR, EDITAR e INSERIR_FICHEIRO.
    2. REGRA DE SEGURANÇA: Antes de fazeres algo, se o utilizador não disser exatamente o nome da tabela (ex: alunos ou produtos), PERGUNTA-LHE primeiro.
    3. REGRA DE MODIFICAÇÃO: Para APAGAR ou EDITAR algo, exige SEMPRE confirmação final do utilizador antes de enviares o comando.
    4. Quando tiveres os dados todos, responde APENAS com a LISTA JSON (começa com "[" e acaba com "]").
    5. REGRA DE DESISTÊNCIA E TENTATIVAS: Se a BD devolver "FALHA NA CONSULTA", tens permissão para fazer UMA (e apenas uma) nova tentativa corrigindo a palavra para o SINGULAR se tiver no plural.
        Se tiver no SINGULAR corrige para PLURAL . Se falhar novamente, ACEITA A DERROTA e avisa o utilizador.
    6. REGRA DE FICHEIROS: Quando o Sistema te informar que o utilizador enviou um ficheiro, analisa as colunas do ficheiro e compara com o esquema da BD. Se as colunas forem compatíveis, confirma com o
        utilizador para saber em que tabela quer inserir e depois usa INSERIR_FICHEIRO. Se as colunas não baterem certo, podes sugerir um mapeamento usando o campo "mapeamento".
    
    FORMATOS DO JSON (Usa a ferramenta certa):
    - INSERIR: {{"comando": "inserir", "tabela": "nome", "dados": {{"coluna": "valor"}}}}
    - CONSULTAR: {{"comando": "consultar", "tabela": "nome", "filtro_coluna": "coluna", "filtro_valor": "valor"}}
    - APAGAR: {{"comando": "apagar", "tabela": "nome", "filtro_coluna": "coluna", "filtro_valor": "valor"}}
    - EDITAR: {{"comando": "editar", "tabela": "nome", "filtro_coluna": "coluna_pesquisa", "filtro_valor": "valor_pesquisa", "dados": {{"coluna_a_mudar": "novo_valor"}}}}
    - INSERIR_FICHEIRO: {{"comando": "inserir_ficheiro", "tabela": "nome", "mapeamento": {{"coluna_bd": "coluna_ficheiro"}}}}
    """
    
    # gera a resposta com o modelo
    resposta_ia = cliente.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=instrucoes_ia
    )
    
    # devolve apenas o texto da resposta
    return resposta_ia.text