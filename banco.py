import sqlite3
import os

DB_NOME = 'financas.db'
if os.path.exists(DB_NOME):
    try:
        os.remove(DB_NOME)
    except:
        pass

def conectar():
    return sqlite3.connect(DB_NOME)

def criar_tabelas():
    conn = conectar()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE receitas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes TEXT,
        ano TEXT,
        salario REAL DEFAULT 0,
        vale REAL DEFAULT 0,
        decimo1 REAL DEFAULT 0,
        decimo2 REAL DEFAULT 0,
        salario_antes_ferias REAL DEFAULT 0,
        ferias REAL DEFAULT 0,
        salario_10_dias_trabalhados_ferias REAL DEFAULT 0,
        vale_ferias REAL DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes TEXT,
        ano TEXT,
        descricao TEXT,
        valor REAL
    )''')
    
    conn.commit()
    conn.close()
    print("✅ Banco criado com todas as colunas!")

def cadastrar_receita(mes, ano, salario, vale, decimo1, decimo2, salario_antes_ferias, ferias, salario_10_dias_trabalhados_ferias, vale_ferias):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM receitas WHERE mes=? AND ano=?", (mes, ano))
    c.execute('''INSERT INTO receitas VALUES (
        NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )''', (mes, ano, salario, vale, decimo1, decimo2, salario_antes_ferias, ferias, salario_10_dias_trabalhados_ferias, vale_ferias))
    conn.commit()
    conn.close()

def listar_receitas(mes, ano):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM receitas WHERE mes=? AND ano=?", (mes, ano))
    dados = c.fetchall()
    conn.close()
    return dados

def calcular_total_receitas(mes, ano):
    conn = conectar()
    c = conn.cursor()
    c.execute('''SELECT COALESCE(
        salario + vale + decimo1 + decimo2 + salario_antes_ferias + ferias + salario_10_dias_trabalhados_ferias + vale_ferias, 0
    ) FROM receitas WHERE mes=? AND ano=?''', (mes, ano))
    res = c.fetchone()
    conn.close()
    return res[0] if res and res[0] else 0.0

def listar_categoria_por_ano(ano, coluna):
    conn = conectar()
    c = conn.cursor()
    sql = f"SELECT mes, {coluna} FROM receitas WHERE ano=? AND {coluna} > 0 ORDER BY id"
    c.execute(sql, (ano,))
    dados = c.fetchall()
    conn.close()
    return dados

def somar_categoria_por_ano(ano, coluna):
    conn = conectar()
    c = conn.cursor()
    sql = f"SELECT COALESCE(SUM({coluna}), 0) FROM receitas WHERE ano=?"
    c.execute(sql, (ano,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0.0

def cadastrar_despesa(mes, ano, descricao, valor):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO despesas VALUES (NULL, ?, ?, ?, ?)",
              (mes, ano, descricao, valor))
    conn.commit()
    conn.close()

def listar_despesas(mes, ano):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM despesas WHERE mes=? AND ano=?", (mes, ano))
    dados = c.fetchall()
    conn.close()
    return dados

def calcular_total_despesas(mes, ano):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM despesas WHERE mes=? AND ano=?", (mes, ano))
    res = c.fetchone()
    conn.close()
    return res[0] if res and res[0] else 0.0

criar_tabelas()