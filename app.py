# ==================================================
# CONTROLE FINANCEIRO — BALANCETE PATRIMONIAL
# Versão Final: Abre Navegador Automaticamente
# ==================================================
from flask import Flask, render_template, request, redirect, url_for, make_response, flash
import sqlite3
from fpdf import FPDF
from datetime import datetime
import webbrowser
import threading
import time

# ==================================================
# INICIALIZAÇÃO DO APLICATIVO
# ==================================================
app = Flask(__name__)
app.secret_key = 'chave_secreta_controle_financeiro_2026'

# ==================================================
# BANCO DE DADOS
# ==================================================
def init_db():
    try:
        conn = sqlite3.connect('financeiro.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lancamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                valor REAL NOT NULL CHECK (valor > 0),
                data TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                usuario TEXT DEFAULT 'principal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso")
    except Exception as erro:
        print(f"❌ Erro ao inicializar banco: {erro}")

init_db()

# ==================================================
# CATEGORIAS COMPLETAS
# ==================================================
CATEGORIAS_ENTRADA = [
    "Salário",
    "Pagamento Recebido",
    "Adiantamento Vale Recebido",
    "13º Salário - 1ª Parcela",
    "13º Salário - 2ª Parcela",
    "Férias",
    "Pagamento antes das Férias",
    "Pagamento 10 Dias Trabalhados",
    "Vale após Férias",
    "Reserva Caixa",
    "Reserva Caixa — Poupança Santander"
]

CATEGORIAS_SAIDA = [
    "Despesas no Pagamento",
    "Despesas no Vale",
    "Despesas nas Férias",
    "Despesas na 1ª Parcela do 13º Salário",
    "Despesas na 2ª Parcela do 13º Salário",
    "Despesas após Férias",
    "Despesas no Pagamento Recebido antes das Férias",
    "Despesas no Pagamento Recebido após as Férias",
    "Despesas no Vale Recebido após Férias",
    "Baixa de Reserva Caixa",
    "Baixa Reserva Caixa — Poupança Santander"
]

# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================
def calcular_saldo_reserva():
    try:
        conn = sqlite3.connect('financeiro.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) 
            FROM lancamentos 
            WHERE categoria IN ('Reserva Caixa', 'Reserva Caixa — Poupança Santander')
        """)
        total_entradas = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) 
            FROM lancamentos 
            WHERE categoria IN ('Baixa de Reserva Caixa', 'Baixa Reserva Caixa — Poupança Santander')
        """)
        total_baixas = cursor.fetchone()[0]
        conn.close()
        return round(total_entradas - total_baixas, 2)
    except Exception as erro:
        print(f"Erro no cálculo da reserva: {erro}")
        return 0.00


def calcular_saldos_gerais():
    try:
        conn = sqlite3.connect('financeiro.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM lancamentos WHERE tipo = 'Entrada'")
        total_entradas = round(cursor.fetchone()[0], 2)
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM lancamentos WHERE tipo = 'Saída'")
        total_saidas = round(cursor.fetchone()[0], 2)
        conn.close()
        saldo_geral = round(total_entradas - total_saidas, 2)
        return {
            'entradas': total_entradas,
            'saidas': total_saidas,
            'saldo_geral': saldo_geral
        }
    except Exception as erro:
        print(f"Erro no cálculo geral: {erro}")
        return {'entradas': 0, 'saidas': 0, 'saldo_geral': 0}

# ==================================================
# ROTAS
# ==================================================
@app.route('/')
def index():
    try:
        conn = sqlite3.connect('financeiro.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tipo, categoria, valor, data, descricao 
            FROM lancamentos 
            ORDER BY data DESC, id DESC
        """)
        lancamentos = cursor.fetchall()
        conn.close()
        saldo_reserva = calcular_saldo_reserva()
        saldos_gerais = calcular_saldos_gerais()
        return render_template(
            'index.html',
            lancamentos=lancamentos,
            categorias_entrada=CATEGORIAS_ENTRADA,
            categorias_saida=CATEGORIAS_SAIDA,
            saldo_reserva=saldo_reserva,
            saldos_gerais=saldos_gerais
        )
    except Exception as erro:
        return f"Erro ao carregar página inicial: {erro}"


@app.route('/adicionar', methods=['POST'])
def adicionar():
    try:
        tipo = request.form.get('tipo', '').strip()
        categoria = request.form.get('categoria', '').strip()
        valor = float(request.form.get('valor', 0))
        data = request.form.get('data', '').strip()
        descricao = request.form.get('descricao', 'Sem observação').strip()
        if not all([tipo, categoria, valor, data]):
            flash("Preencha todos os campos obrigatórios!", "erro")
            return redirect(url_for('index'))
        if valor <= 0:
            flash("O valor deve ser maior que zero!", "erro")
            return redirect(url_for('index'))
        conn = sqlite3.connect('financeiro.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO lancamentos (tipo, categoria, valor, data, descricao)
            VALUES (?, ?, ?, ?, ?)
        """, (tipo, categoria, valor, data, descricao))
        conn.commit()
        conn.close()
        flash(f"✅ Lançamento registrado: {categoria} — R$ {valor:.2f}", "sucesso")
        return redirect(url_for('index'))
    except Exception as erro:
        flash(f"❌ Erro ao registrar: {erro}", "erro")
        return redirect(url_for('index'))


@app.route('/excluir/<int:lancamento_id>')
def excluir(lancamento_id):
    try:
        conn = sqlite3.connect('financeiro.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lancamentos WHERE id = ?", (lancamento_id,))
        conn.commit()
        conn.close()
        flash("🗑️ Lançamento excluído com sucesso!", "sucesso")
        return redirect(url_for('index'))
    except Exception as erro:
        flash(f"❌ Erro ao excluir: {erro}", "erro")
        return redirect(url_for('index'))


@app.route('/editar/<int:lancamento_id>', methods=['GET', 'POST'])
def editar(lancamento_id):
    conn = sqlite3.connect('financeiro.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        tipo = request.form.get('tipo', '')
        categoria = request.form.get('categoria', '')
        valor = float(request.form.get('valor', 0))
        data = request.form.get('data', '')
        descricao = request.form.get('descricao', '')
        cursor.execute("""
            UPDATE lancamentos 
            SET tipo = ?, categoria = ?, valor = ?, data = ?, descricao = ?
            WHERE id = ?
        """, (tipo, categoria, valor, data, descricao, lancamento_id))
        conn.commit()
        conn.close()
        flash("✏️ Lançamento atualizado!", "sucesso")
        return redirect(url_for('index'))
    cursor.execute("""
        SELECT id, tipo, categoria, valor, data, descricao 
        FROM lancamentos WHERE id = ?
    """, (lancamento_id,))
    lancamento = cursor.fetchone()
    conn.close()
    return render_template(
        'editar.html',
        lancamento=lancamento,
        categorias_entrada=CATEGORIAS_ENTRADA,
        categorias_saida=CATEGORIAS_SAIDA
    )


@app.route('/relatorio-pdf')
def relatorio_pdf():
    try:
        conn = sqlite3.connect('financeiro.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tipo, categoria, valor, data, descricao 
            FROM lancamentos ORDER BY data, id
        """)
        lancamentos = cursor.fetchall()
        conn.close()
        saldo_reserva = calcular_saldo_reserva()
        saldos = calcular_saldos_gerais()
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 12, "CONTROLE FINANCEIRO — BALANCETE", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "RESUMO GERAL", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(95, 8, f"Total de Entradas:  R$ {saldos['entradas']:,.2f}", border=1)
        pdf.cell(95, 8, f"Total de Saídas:     R$ {saldos['saidas']:,.2f}", border=1, ln=True)
        pdf.cell(95, 8, f"Saldo Geral:         R$ {saldos['saldo_geral']:,.2f}", border=1)
        pdf.cell(95, 8, f"Saldo Reserva:       R$ {saldo_reserva:,.2f}", border=1, ln=True)
        pdf.ln(8)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(28, 8, "Data", 1, 0, 'C')
        pdf.cell(25, 8, "Tipo", 1, 0, 'C')
        pdf.cell(55, 8, "Categoria", 1, 0, 'C')
        pdf.cell(30, 8, "Valor R$", 1, 0, 'C')
        pdf.cell(62, 8, "Descrição", 1, 1, 'C')
        
        pdf.set_font("Arial", size=9)
        for lanc in lancamentos:
            cor = (0, 128, 0) if lanc[0] == 'Entrada' else (200, 0, 0)
            pdf.set_text_color(*cor)
            pdf.cell(28, 7, lanc[3], 1)
            pdf.cell(25, 7, lanc[0], 1)
            pdf.cell(55, 7, lanc[1], 1)
            pdf.cell(30, 7, f"{lanc[2]:,.2f}", 1, 0, 'R')
            pdf.cell(62, 7, lanc[4] or '-', 1, 1)
        
        pdf.set_text_color(0, 0, 0)
        arquivo_pdf = pdf.output(dest='S').encode('latin-1')
        resposta = make_response(arquivo_pdf)
        resposta.headers['Content-Type'] = 'application/pdf'
        resposta.headers['Content-Disposition'] = f'attachment; filename=balancete_{datetime.now().strftime("%Y%m%d")}.pdf'
        return resposta
    except Exception as erro:
        return f"Erro ao gerar PDF: {erro}"

# ==================================================
# ABRIR NAVEGADOR AUTOMATICAMENTE
# ==================================================
def abrir_navegador():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

# ==================================================
# EXECUÇÃO
# ==================================================
if __name__ == '__main__':
    print("="*50)
    print("🚀 Iniciando Controle Financeiro...")
    print("📍 Abrindo: http://127.0.0.1:5000")
    print("="*50)
    
    threading.Thread(target=abrir_navegador, daemon=True).start()
    app.run(debug=False)