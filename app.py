# ==================================================
# CONTROLE FINANCEIRO — FILTROS VISÍVEIS E FUNCIONANDO
# ==================================================
from flask import Flask, render_template, request, redirect, url_for, make_response, flash
import sqlite3
from fpdf import FPDF
from datetime import datetime
import webbrowser
import threading
import time

app = Flask(__name__)
app.secret_key = 'chave_secreta_controle_financeiro_2026'

# ==================================================
# BANCO DE DADOS
# ==================================================
def init_db():
    try:
        conn = sqlite3.connect('financeiro.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS lancamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                valor REAL NOT NULL,
                data TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                status TEXT DEFAULT 'Oficial'
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado")
    except Exception as e:
        print(f"❌ Erro no banco: {e}")

init_db()

# ==================================================
# CATEGORIAS
# ==================================================
CAT_ENTRADA = [
    "Salario",
    "Pagamento Recebido",
    "Adiantamento Vale Recebido",
    "13 Salario - 1 Parcela",
    "13 Salario - 2 Parcela",
    "Ferias",
    "Pagamento antes das Ferias",
    "Pagamento 10 Dias Trabalhados",
    "Vale apos as Ferias",
    "Reserva Caixa Poupanca Santander"
]

CAT_SAIDA = [
    "Despesas no Pagamento",
    "Despesas no Vale",
    "Despesas nas Ferias",
    "Despesa - 1 Parcela 13 Salario",
    "Despesa - 2 Parcela 13 Salario",
    "Despesas apos Ferias",
    "Despesas antes das Ferias",
    "Despesas com Vale Recebido",
    "Baixa Reserva Caixa Poupanca Santander"
]

# ==================================================
# FUNÇÕES DE CÁLCULO
# ==================================================
def calcular_saldo_reserva():
    try:
        conn = sqlite3.connect('financeiro.db')
        c = conn.cursor()
        c.execute("""
            SELECT COALESCE(SUM(valor), 0) FROM lancamentos
            WHERE status = 'Oficial' AND categoria = 'Reserva Caixa Poupanca Santander'
        """)
        entradas = c.fetchone()[0] or 0
        c.execute("""
            SELECT COALESCE(SUM(valor), 0) FROM lancamentos
            WHERE status = 'Oficial' AND categoria = 'Baixa Reserva Caixa Poupanca Santander'
        """)
        saidas = c.fetchone()[0] or 0
        conn.close()
        return round(entradas - saidas, 2)
    except Exception as e:
        print(f"Erro saldo reserva: {e}")
        return 0.0

def calcular_saldos_gerais(mes=None, filtro_tipo=None):
    try:
        conn = sqlite3.connect('financeiro.db')
        c = conn.cursor()
        
        params_ent = []
        cond_ent = ["status = 'Oficial' AND tipo = 'Entrada'"]
        if mes:
            cond_ent.append("strftime('%Y-%m', data) = ?")
            params_ent.append(mes)
        if filtro_tipo and filtro_tipo != 'entradas':
            if filtro_tipo == 'reserva':
                cond_ent.append("categoria = 'Reserva Caixa Poupanca Santander'")
            elif filtro_tipo == 'baixa_reserva':
                cond_ent = ["status = 'Oficial' AND tipo = 'Saida' AND categoria = 'Baixa Reserva Caixa Poupanca Santander'"]
            elif filtro_tipo == 'saidas':
                cond_ent = ["status = 'Oficial' AND tipo = 'Saida'"]
            elif filtro_tipo == 'futuros':
                cond_ent = ["status = 'Futuro' AND tipo = 'Entrada'"]
        
        where_ent = " AND ".join(cond_ent)
        c.execute(f"SELECT COALESCE(SUM(valor), 0) FROM lancamentos WHERE {where_ent}", params_ent)
        total_entradas = round(c.fetchone()[0] or 0, 2)

        params_sai = []
        cond_sai = ["status = 'Oficial' AND tipo = 'Saida'"]
        if mes:
            cond_sai.append("strftime('%Y-%m', data) = ?")
            params_sai.append(mes)
        if filtro_tipo and filtro_tipo != 'saidas':
            if filtro_tipo == 'baixa_reserva':
                cond_sai = ["status = 'Oficial' AND tipo = 'Saida' AND categoria = 'Baixa Reserva Caixa Poupanca Santander'"]
            elif filtro_tipo == 'reserva':
                cond_sai = ["1=0"]
            elif filtro_tipo == 'entradas':
                cond_sai = ["1=0"]
            elif filtro_tipo == 'futuros':
                cond_sai = ["status = 'Futuro' AND tipo = 'Saida'"]
        
        where_sai = " AND ".join(cond_sai)
        c.execute(f"SELECT COALESCE(SUM(valor), 0) FROM lancamentos WHERE {where_sai}", params_sai)
        total_saidas = round(c.fetchone()[0] or 0, 2)

        cond_fut = ["status = 'Futuro'"]
        params_fut = []
        if mes:
            cond_fut.append("strftime('%Y-%m', data) = ?")
            params_fut.append(mes)
        if filtro_tipo == 'futuros':
            pass
        elif filtro_tipo:
            cond_fut.append("(1=1)")
        
        where_fut = " AND ".join(cond_fut)
        c.execute(f"SELECT COUNT(*), COALESCE(SUM(valor), 0) FROM lancamentos WHERE {where_fut}", params_fut)
        qtd_futuros, soma_futuros = c.fetchone()
        
        conn.close()
        return {
            'entradas': total_entradas,
            'saidas': total_saidas,
            'saldo_geral': round(total_entradas - total_saidas, 2),
            'qtd_futuros': qtd_futuros,
            'soma_futuros': round(soma_futuros or 0, 2)
        }
    except Exception as e:
        print(f"Erro saldos: {e}")
        return {'entradas':0,'saidas':0,'saldo_geral':0,'qtd_futuros':0,'soma_futuros':0}

def listar_meses_disponiveis():
    try:
        conn = sqlite3.connect('financeiro.db')
        c = conn.cursor()
        c.execute("SELECT DISTINCT strftime('%Y-%m', data) as mes FROM lancamentos ORDER BY mes DESC")
        meses = [row[0] for row in c.fetchall()]
        conn.close()
        return meses
    except Exception as e:
        print(f"Erro listar meses: {e}")
        return []

# ==================================================
# ROTAS
# ==================================================
@app.route('/')
def index():
    try:
        mes = request.args.get('mes', '')
        filtro_tipo = request.args.get('filtro_tipo', '')
        
        conn = sqlite3.connect('financeiro.db')
        c = conn.cursor()
        
        condicoes = []
        params = []
        
        if mes:
            condicoes.append("strftime('%Y-%m', data) = ?")
            params.append(mes)
        
        if filtro_tipo == 'entradas':
            condicoes.append("tipo = 'Entrada'")
        elif filtro_tipo == 'saidas':
            condicoes.append("tipo = 'Saida'")
        elif filtro_tipo == 'reserva':
            condicoes.append("categoria = 'Reserva Caixa Poupanca Santander'")
        elif filtro_tipo == 'baixa_reserva':
            condicoes.append("categoria = 'Baixa Reserva Caixa Poupanca Santander'")
        elif filtro_tipo == 'futuros':
            condicoes.append("status = 'Futuro'")
        
        where_sql = "WHERE " + " AND ".join(condicoes) if condicoes else ""
        
        c.execute(f"""
            SELECT id, tipo, categoria, valor, data, descricao, status 
            FROM lancamentos {where_sql} ORDER BY data DESC, id DESC
        """, params)
        lancamentos = c.fetchall()
        conn.close()
        
        return render_template(
            'index.html',
            lancamentos=lancamentos,
            categorias_entrada=CAT_ENTRADA,
            categorias_saida=CAT_SAIDA,
            saldo_reserva=calcular_saldo_reserva(),
            saldos_gerais=calcular_saldos_gerais(mes, filtro_tipo),
            meses=listar_meses_disponiveis(),
            mes_selecionado=mes,
            filtro_tipo=filtro_tipo
        )
    except Exception as e:
        return f"Erro ao carregar página: {str(e)}"

@app.route('/adicionar', methods=['POST'])
def adicionar():
    tipo = request.form.get('tipo')
    categoria = request.form.get('categoria')
    valor = float(request.form.get('valor'))
    data = request.form.get('data')
    descricao = request.form.get('descricao', '')
    status = request.form.get('status', 'Oficial')
    
    if not all([tipo, categoria, valor, data]):
        flash("Preencha todos os campos!", "erro")
        return redirect(url_for('index'))
    
    try:
        conn = sqlite3.connect('financeiro.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO lancamentos (tipo, categoria, valor, data, descricao, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tipo, categoria, valor, data, descricao, status))
        conn.commit()
        conn.close()
        flash(f"✅ Lançamento registrado: {categoria} - R$ {valor:.2f}", "sucesso")
    except Exception as e:
        flash(f"Erro: {str(e)}", "erro")
    return redirect(url_for('index'))

@app.route('/converter-oficial/<int:lanc_id>')
def converter_oficial(lanc_id):
    try:
        conn = sqlite3.connect('financeiro.db')
        c = conn.cursor()
        c.execute("UPDATE lancamentos SET status = 'Oficial' WHERE id = ?", (lanc_id,))
        conn.commit()
        conn.close()
        flash("✅ Convertido para Oficial!", "sucesso")
    except Exception as e:
        flash(f"Erro: {str(e)}", "erro")
    return redirect(url_for('index'))

@app.route('/excluir/<int:lanc_id>')
def excluir(lanc_id):
    try:
        conn = sqlite3.connect('financeiro.db')
        c = conn.cursor()
        c.execute("DELETE FROM lancamentos WHERE id = ?", (lanc_id,))
        conn.commit()
        conn.close()
        flash("🗑️ Excluído!", "sucesso")
    except Exception as e:
        flash(f"Erro: {str(e)}", "erro")
    return redirect(url_for('index'))

@app.route('/editar/<int:lanc_id>', methods=['GET', 'POST'])
def editar(lanc_id):
    conn = sqlite3.connect('financeiro.db')
    c = conn.cursor()
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        valor = float(request.form.get('valor'))
        data = request.form.get('data')
        descricao = request.form.get('descricao', '')
        status = request.form.get('status', 'Oficial')
        c.execute("""
            UPDATE lancamentos SET tipo=?, categoria=?, valor=?, data=?, descricao=?, status=?
            WHERE id=?
        """, (tipo, categoria, valor, data, descricao, status, lanc_id))
        conn.commit()
        conn.close()
        flash("✏️ Atualizado!", "sucesso")
        return redirect(url_for('index'))
    c.execute("SELECT id, tipo, categoria, valor, data, descricao, status FROM lancamentos WHERE id = ?", (lanc_id,))
    lanc = c.fetchone()
    conn.close()
    return render_template('editar.html', lancamento=lanc, categorias_entrada=CAT_ENTRADA, categorias_saida=CAT_SAIDA)

@app.route('/relatorio-pdf')
def relatorio_pdf():
    try:
        mes = request.args.get('mes', '')
        filtro_tipo = request.args.get('filtro_tipo', '')
        
        conn = sqlite3.connect('financeiro.db')
        c = conn.cursor()
        
        condicoes = []
        params = []
        if mes:
            condicoes.append("strftime('%Y-%m', data) = ?")
            params.append(mes)
        if filtro_tipo == 'entradas':
            condicoes.append("tipo = 'Entrada'")
        elif filtro_tipo == 'saidas':
            condicoes.append("tipo = 'Saida'")
        elif filtro_tipo == 'reserva':
            condicoes.append("categoria = 'Reserva Caixa Poupanca Santander'")
        elif filtro_tipo == 'baixa_reserva':
            condicoes.append("categoria = 'Baixa Reserva Caixa Poupanca Santander'")
        elif filtro_tipo == 'futuros':
            condicoes.append("status = 'Futuro'")
        
        where_sql = "WHERE " + " AND ".join(condicoes) if condicoes else ""
        c.execute(f"SELECT tipo, categoria, valor, data, descricao, status FROM lancamentos {where_sql} ORDER BY data, id", params)
        lancamentos = c.fetchall()
        conn.close()
        
        saldo_reserva = calcular_saldo_reserva()
        saldos = calcular_saldos_gerais(mes, filtro_tipo)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 12, "CONTROLE FINANCEIRO - BALANCETE", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
        if mes or filtro_tipo:
            filtro_nome = {
                'entradas': 'Entradas', 'saidas': 'Saidas',
                'reserva': 'Reserva de Caixa', 'baixa_reserva': 'Baixa de Reserva',
                'futuros': 'Lançamentos Futuros'
            }.get(filtro_tipo, '')
            pdf.cell(0, 8, f"Filtro: Mês {mes or 'Todos'} | {filtro_nome or 'Todos'}", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "RESUMO", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(95, 8, f"Entradas: R$ {saldos['entradas']:.2f}", border=1)
        pdf.cell(95, 8, f"Saidas: R$ {saldos['saidas']:.2f}", border=1, ln=True)
        pdf.cell(95, 8, f"Saldo: R$ {saldos['saldo_geral']:.2f}", border=1)
        pdf.cell(95, 8, f"Reserva Total: R$ {saldo_reserva:.2f}", border=1, ln=True)
        if saldos['qtd_futuros'] > 0:
            pdf.ln(3)
            pdf.cell(0, 8, f"Futuros: {saldos['qtd_futuros']} lançamento(s) - R$ {saldos['soma_futuros']:.2f}", ln=True)
        pdf.ln(8)
        
        w_data, w_status, w_tipo, w_cat, w_valor, w_desc = 22, 20, 18, 42, 25, 68
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(w_data, 7, "Data", 1, 0, 'C')
        pdf.cell(w_status, 7, "Status", 1, 0, 'C')
        pdf.cell(w_tipo, 7, "Tipo", 1, 0, 'C')
        pdf.cell(w_cat, 7, "Categoria", 1, 0, 'C')
        pdf.cell(w_valor, 7, "Valor", 1, 0, 'C')
        pdf.cell(w_desc, 7, "Descricao", 1, 1, 'C')
        
        pdf.set_font("Arial", size=8)
        for l in lancamentos:
            pdf.set_text_color(204, 153, 0) if l[5] == 'Futuro' else (pdf.set_text_color(0, 128, 0) if l[0] == 'Entrada' else pdf.set_text_color(200, 0, 0))
            desc = str(l[4]) if l[4] else '-'
            x_inicial = pdf.get_x()
            y_inicial = pdf.get_y()
            pdf.multi_cell(w_data, 6, str(l[3]), 1, 'L')
            pdf.set_xy(x_inicial + w_data, y_inicial)
            pdf.multi_cell(w_status, 6, str(l[5]), 1, 'L')
            pdf.set_xy(x_inicial + w_data + w_status, y_inicial)
            pdf.multi_cell(w_tipo, 6, str(l[0]), 1, 'L')
            pdf.set_xy(x_inicial + w_data + w_status + w_tipo, y_inicial)
            pdf.multi_cell(w_cat, 6, str(l[1]), 1, 'L')
            pdf.set_xy(x_inicial + w_data + w_status + w_tipo + w_cat, y_inicial)
            pdf.multi_cell(w_valor, 6, f"{l[2]:.2f}", 1, 'R')
            pdf.set_xy(x_inicial + w_data + w_status + w_tipo + w_cat + w_valor, y_inicial)
            pdf.multi_cell(w_desc, 6, desc, 1, 'L')
            pdf.ln()
        
        pdf.set_text_color(0, 0, 0)
        resposta = make_response(pdf.output(dest='S').encode('latin-1', errors='replace'))
        resposta.headers['Content-Type'] = 'application/pdf'
        resposta.headers['Content-Disposition'] = 'attachment; filename=balancete.pdf'
        return resposta
    except Exception as e:
        return f"Erro PDF: {str(e)}"

def abrir_navegador():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    print("="*50)
    print("🚀 Controle Financeiro - Filtros Corrigidos")
    print("📍 Acesse: http://127.0.0.1:5000")
    print("="*50)
    threading.Thread(target=abrir_navegador, daemon=True).start()
    app.run(debug=False)