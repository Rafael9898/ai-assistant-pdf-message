import sqlite3

# define o nome do ficheiro da bd
NOME_BD = "banco_de_dados.db"

def configurar_bd():
    # liga-se ao ficheiro
    conn = sqlite3.connect(NOME_BD)
    conn.close()

def obter_esquema_bd():
    # le as tabelas e colunas que existem na bd
    conn = sqlite3.connect(NOME_BD)
    cursor = conn.cursor()

    # procura todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
    tabelas = cursor.fetchall()

    esquema_dinamico = {}
    # guarda as colunas de cada tabela
    for tabela in tabelas:
        nome_tabela = tabela[0]
        cursor.execute(f"PRAGMA table_info({nome_tabela});")
        colunas = cursor.fetchall()
        esquema_dinamico[nome_tabela] = {col[1]: col[2] for col in colunas}

    conn.close()
    return esquema_dinamico

def inserir_registo(nome_tabela, dados):
    # prepara as colunas e os valores
    colunas = ", ".join(dados.keys())
    interrogacoes = ", ".join(["?"] * len(dados))
    valores = tuple(dados.values())
    
    # monta o comando sql para inserir
    query_sql = f"INSERT INTO {nome_tabela} ({colunas}) VALUES ({interrogacoes})"
    
    # executa e guarda na bd
    conn = sqlite3.connect(NOME_BD)
    cursor = conn.cursor()
    cursor.execute(query_sql, valores)
    conn.commit()
    conn.close()

def consultar_registos(nome_tabela, coluna_filtro="", valor_filtro=""):
    conn = sqlite3.connect(NOME_BD)
    cursor = conn.cursor()
    
    # se houver filtro vai procurar
    if coluna_filtro and valor_filtro:
        query = f"SELECT * FROM {nome_tabela} WHERE {coluna_filtro} LIKE ?"
        cursor.execute(query, (f"%{valor_filtro}%",))
    else:
        # mostra tudo
        query = f"SELECT * FROM {nome_tabela}"
        cursor.execute(query)
        
    resultados = cursor.fetchall()
    
    # guarda os nomes das colunas
    colunas = [descricao[0] for descricao in cursor.description]
    conn.close()
    
    #junta colunas e valores numa lista
    lista_resultados = []
    for linha in resultados:
        lista_resultados.append(dict(zip(colunas, linha)))
        
    return lista_resultados

def apagar_registo(nome_tabela, coluna_filtro, valor_filtro):
    conn = sqlite3.connect(NOME_BD)
    cursor = conn.cursor()
    
    # apaga usando pesquisa
    query = f"DELETE FROM {nome_tabela} WHERE {coluna_filtro} LIKE ?"
    cursor.execute(query, (f"%{valor_filtro}%",))
    
    # ve quantas linhas apagou
    linhas_apagadas = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return linhas_apagadas

def editar_registo(nome_tabela, coluna_filtro, valor_filtro, dados_novos):
    conn = sqlite3.connect(NOME_BD)
    cursor = conn.cursor()
    
    # prepara os novos valores
    colunas_set = ", ".join([f"{k} = ?" for k in dados_novos.keys()])
    valores = list(dados_novos.values())
    
    # adiciona o valor da pesquisa ao fim da lista
    valores.append(f"%{valor_filtro}%")
    
    # executa o comando para atualizar
    query = f"UPDATE {nome_tabela} SET {colunas_set} WHERE {coluna_filtro} LIKE ?"
    cursor.execute(query, tuple(valores))
    
    #ve quantas linhas mudou
    linhas_afetadas = cursor.rowcount
    conn.commit()
    conn.close()
    
    return linhas_afetadas