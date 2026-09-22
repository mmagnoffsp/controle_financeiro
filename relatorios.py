from fpdf import FPDF
from banco import (
    listar_receitas, listar_despesas, calcular_total_receitas, calcular_total_despesas,
    listar_categoria_por_ano, somar_categoria_por_ano
)

def limpar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.replace("\u2014", "-").replace("\u2013", "-")
    texto = texto.replace("—", "-").replace("–", "-")
    texto = texto.replace("á", "a").replace("é", "e").replace("í", "i")
    texto = texto.replace("ó", "o").replace("ú", "u")
    texto = texto.replace("â", "a").replace("ê", "e").replace("ô", "o")
    texto = texto.replace("ã", "a").replace("õ", "o").replace("ç", "c")
    return texto

def exportar_pdf(mes, ano):
    mes_limpo = limpar_texto(mes)
    ano_limpo = limpar_texto(ano)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(190, 12, txt="CONTROLE FINANCEIRO - " + mes_limpo + "/" + ano_limpo, ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, txt="RECEITAS", ln=True)
    
    rec = listar_receitas(mes, ano)
    if rec:
        r = rec[0]
        itens = [
            ("Salario recebido", r[3]),
            ("Adiantamento vale", r[4]),
            ("13 - 1a Parcela", r[5]),
            ("13 - 2a Parcela", r[6]),
            ("Salario antes das ferias", r[7]),
            ("Ferias", r[8]),
            ("Salario recebido dos 10 dias trabalhados das ferias", r[9]),
            ("Vale apos as ferias", r[10]),
        ]
        total_rec = sum(v for _, v in itens)
        
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(110, 8, txt="Item", border=1, fill=True)
        pdf.cell(70, 8, txt="Valor (R$)", border=1, fill=True, align='R')
        pdf.ln()
        
        pdf.set_font("Arial", '', 11)
        for nome, valor in itens:
            pdf.cell(110, 7, txt=nome, border=1)
            pdf.cell(70, 7, txt=f"{valor:.2f}", border=1, align='R')
            pdf.ln()
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(110, 9, txt="TOTAL DE RECEITAS", border=1)
        pdf.cell(70, 9, txt=f"{total_rec:.2f}", border=1, align='R')
        pdf.ln(10)
    else:
        pdf.cell(190, 8, txt="Sem registros de receitas", ln=True)
        pdf.ln(5)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, txt="DESPESAS", ln=True)
    
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(110, 8, txt="Descricao da despesa", border=1, fill=True)
    pdf.cell(70, 8, txt="Valor (R$)", border=1, fill=True, align='R')
    pdf.ln()
    
    deb = listar_despesas(mes, ano)
    pdf.set_font("Arial", '', 11)
    for d in deb:
        desc = limpar_texto(d[3])
        pdf.cell(110, 7, txt=desc, border=1)
        pdf.cell(70, 7, txt=f"{d[4]:.2f}", border=1, align='R')
        pdf.ln()
    
    total_deb = calcular_total_despesas(mes, ano)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(110, 9, txt="TOTAL DE DESPESAS", border=1)
    pdf.cell(70, 9, txt=f"{total_deb:.2f}", border=1, align='R')
    pdf.ln(10)

    saldo = calcular_total_receitas(mes, ano) - total_deb
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 150, 0) if saldo >= 0 else pdf.set_text_color(200, 0, 0)
    pdf.cell(190, 10, txt=f"SALDO FINAL: R$ {saldo:.2f}", ln=True)

    nome_arq = f"financas_{mes_limpo}_{ano_limpo}.pdf"
    pdf.output(nome_arq)
    print(f"✅ PDF gerado: {nome_arq}")

def exportar_relatorio_categoria(ano, coluna, titulo):
    ano_limpo = limpar_texto(ano)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 12, txt=f"{titulo} - Ano {ano_limpo}", ln=True, align='C')
    pdf.ln(8)

    MESES_ORDEM = {
        "Janeiro": 1, "Fevereiro": 2, "Marco": 3, "Abril": 4, "Maio": 5, "Junho": 6,
        "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }

    dados = listar_categoria_por_ano(ano, coluna)
    dados_ordenados = sorted(dados, key=lambda x: MESES_ORDEM.get(x[0], 99))

    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(80, 10, txt="MES", border=1, fill=True, align='C')
    pdf.cell(110, 10, txt="VALOR RECEBIDO", border=1, fill=True, align='C')
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 11)
    
    for mes, valor in dados_ordenados:
        valor = valor or 0
        pdf.cell(80, 9, txt=limpar_texto(mes), border=1, align='C')
        pdf.cell(110, 9, txt=f"R$ {valor:.2f}", border=1, align='R')
        pdf.ln()

    total_ano = somar_categoria_por_ano(ano, coluna)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(80, 11, txt="TOTAL DO ANO", border=1, fill=True)
    pdf.cell(110, 11, txt=f"R$ {total_ano:.2f}", border=1, fill=True, align='R')
    pdf.ln(15)

    nome_arq = f"relatorio_{coluna}_{ano_limpo}.pdf"
    pdf.output(nome_arq)
    print(f"✅ Relatório gerado: {nome_arq}")
    return nome_arq