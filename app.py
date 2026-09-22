import tkinter as tk
from tkinter import ttk, messagebox
from banco import calcular_total_receitas, calcular_total_despesas, cadastrar_receita, cadastrar_despesa, listar_receitas, listar_despesas
from relatorios import exportar_pdf, exportar_relatorio_categoria

root = tk.Tk()
root.title("CONTROLE FINANCEIRO")
root.geometry("950x900")
root.configure(bg="#f0f4f8")

mes_atual = tk.StringVar(value="Setembro")
ano_atual = tk.StringVar(value="2026")
ano_relatorio = tk.StringVar(value="2026")

MESES = ["Janeiro","Fevereiro","Marco","Abril","Maio","Junho",
         "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

COR_FUNDO = "#f0f4f8"
COR_CABECALHO = "#2c3e50"
COR_RECEITAS = "#27ae60"
COR_DESPESAS = "#e74c3c"
COR_SALDO = "#3498db"
COR_DESTAQUE = "#d35400"
COR_RELATORIO = "#8e44ad"

def atualizar_dashboard():
    m = mes_atual.get()
    a = ano_atual.get()
    total_rec = calcular_total_receitas(m, a)
    total_des = calcular_total_despesas(m, a)
    saldo = total_rec - total_des
    
    lbl_rec_valor.config(text=f"R$ {total_rec:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    lbl_des_valor.config(text=f"R$ {total_des:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    lbl_saldo_valor.config(text=f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    lbl_saldo_valor.config(fg="#27ae60" if saldo >= 0 else "#e74c3c")
    carregar_lancamentos(m, a)

def carregar_lancamentos(m, a):
    for item in tree.get_children():
        tree.delete(item)
    for r in listar_receitas(m, a):
        total_r = sum(r[3:]) if len(r) > 3 else 0
        tree.insert("", "end", values=(
            "Receitas do mês",
            f"R$ {total_r:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            "RECEITA"
        ))
    for d in listar_despesas(m, a):
        tree.insert("", "end", values=(
            d[3],
            f"R$ {d[4]:.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            "DESPESA"
        ))

def janela_cadastrar_receita():
    win = tk.Toplevel(root)
    win.title("LANÇAR RECEITA")
    win.geometry("750x520")  # Tamanho fixo — TUDO VISÍVEL!
    win.configure(bg=COR_FUNDO)
    
    tk.Label(win, text=f"MÊS: {mes_atual.get()}  |  ANO: {ano_atual.get()}",
             font=("Arial", 12, "bold"), bg=COR_FUNDO, fg=COR_CABECALHO).pack(pady=12)

    # Variáveis para os valores
    v_salario = tk.StringVar()
    v_vale = tk.StringVar()
    v_dec1 = tk.StringVar()
    v_dec2 = tk.StringVar()
    v_sal_antes = tk.StringVar()
    v_ferias = tk.StringVar()
    v_10dias = tk.StringVar()
    v_vale_ferias = tk.StringVar()

    # Função para criar linha com botão de seleção + campo valor
    def criar_linha(container, texto, var_valor, cor_texto=COR_CABECALHO):
        frame_linha = tk.Frame(container, bg=COR_FUNDO)
        frame_linha.pack(fill="x", pady=5)
        
        # Botão seletor (apenas rótulo destacado)
        lbl = tk.Label(frame_linha, text=texto, font=("Arial", 10, "bold"),
                       bg=COR_FUNDO, fg=cor_texto, width=45, anchor="w")
        lbl.pack(side="left", padx=5)
        
        tk.Label(frame_linha, text="R$", bg=COR_FUNDO, font=("Arial", 10)).pack(side="left")
        ent = tk.Entry(frame_linha, textvariable=var_valor, width=18, font=("Arial", 11))
        ent.pack(side="left", padx=5)
        return ent

    # Conteúdo organizado em 2 colunas para CABER TUDO!
    esquerda = tk.Frame(win, bg=COR_FUNDO)
    direita = tk.Frame(win, bg=COR_FUNDO)
    esquerda.pack(side="left", fill="both", expand=True, padx=15, pady=5)
    direita.pack(side="left", fill="both", expand=True, padx=15, pady=5)

    tk.Label(esquerda, text="💵 VALORES — PARTE 1", font=("Arial", 11, "bold"),
             bg=COR_FUNDO, fg=COR_RECEITAS).pack(pady=(0,8))
    
    criar_linha(esquerda, "Salário Recebido", v_salario)
    criar_linha(esquerda, "Adiantamento Vale", v_vale)
    criar_linha(esquerda, "13º Salário — 1ª Parcela", v_dec1)
    criar_linha(esquerda, "13º Salário — 2ª Parcela", v_dec2)

    tk.Label(direita, text="🏖️ VALORES — PARTE 2", font=("Arial", 11, "bold"),
             bg=COR_FUNDO, fg=COR_DESTAQUE).pack(pady=(0,8))
    
    criar_linha(direita, "Salário ANTES das Férias", v_sal_antes)
    criar_linha(direita, "Férias Recebidas", v_ferias)
    
    # ⭐ DESTAQUE — SEMPRE VISÍVEL!
    criar_linha(direita, "⭐ 10 DIAS TRABALHADOS DAS FÉRIAS", v_10dias, COR_DESTAQUE)
    
    criar_linha(direita, "Vale após as Férias", v_vale_ferias)

    def converter(val):
        t = val.get().strip()
        return float(t.replace(',', '.')) if t else 0.0

    def salvar():
        cadastrar_receita(
            mes_atual.get(), ano_atual.get(),
            converter(v_salario), converter(v_vale),
            converter(v_dec1), converter(v_dec2),
            converter(v_sal_antes), converter(v_ferias),
            converter(v_10dias), converter(v_vale_ferias)
        )
        messagebox.showinfo("SUCESSO ✅", "Valores salvos com sucesso!")
        atualizar_dashboard()
        win.destroy()

    tk.Button(win, text="💾 SALVAR LANÇAMENTO", command=salvar,
              bg=COR_RECEITAS, fg="white", font=("Arial", 12, "bold"),
              padx=50, pady=12).pack(pady=20)

def janela_cadastrar_despesa():
    win = tk.Toplevel(root)
    win.title("LANÇAR DESPESA")
    win.geometry("480x320")
    win.configure(bg=COR_FUNDO)
    
    tk.Label(win, text=f"MÊS: {mes_atual.get()}  |  ANO: {ano_atual.get()}",
             font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_CABECALHO).pack(pady=15)
    
    tk.Label(win, text="Descrição da despesa:", bg=COR_FUNDO, font=("Arial", 10)).pack(anchor="w", padx=30)
    desc = tk.Entry(win, width=50, font=("Arial", 11))
    desc.pack(pady=5, padx=30)
    
    tk.Label(win, text="Valor R$:", bg=COR_FUNDO, font=("Arial", 10)).pack(anchor="w", padx=30, pady=(15,0))
    valor = tk.Entry(win, width=30, font=("Arial", 11))
    valor.pack(pady=5, padx=30)
    
    def salvar():
        d = desc.get().strip()
        v = float(valor.get().replace(',', '.'))
        cadastrar_despesa(mes_atual.get(), ano_atual.get(), d, v)
        messagebox.showinfo("SUCESSO ✅", "Despesa salva!")
        atualizar_dashboard()
        win.destroy()
    
    tk.Button(win, text="💾 SALVAR DESPESA", command=salvar,
              bg=COR_DESPESAS, fg="white", font=("Arial", 11, "bold"),
              padx=40, pady=10).pack(pady=20)

def gerar_pdf_mensal():
    exportar_pdf(mes_atual.get(), ano_atual.get())
    messagebox.showinfo("SUCESSO ✅", "PDF do mês gerado na pasta!")

def gerar_relatorio(coluna, titulo):
    ano = ano_relatorio.get().strip()
    if not ano:
        messagebox.showwarning("Aviso ⚠️", "Digite o ano!")
        return
    arquivo = exportar_relatorio_categoria(ano, coluna, titulo)
    messagebox.showinfo("SUCESSO ✅", f"Relatório gerado!\n{arquivo}")

# ========== CABEÇALHO ==========
topo = tk.Frame(root, bg=COR_CABECALHO, height=80)
topo.pack(fill="x")
topo.pack_propagate(False)
tk.Label(topo, text="CONTROLE FINANCEIRO", font=("Arial", 20, "bold"),
         bg=COR_CABECALHO, fg="white").pack(side="left", padx=30, pady=20)

seletor = tk.Frame(topo, bg=COR_CABECALHO)
seletor.pack(side="right", padx=20)
ttk.Combobox(seletor, textvariable=mes_atual, values=MESES,
             width=12, state="readonly").pack(side="left", padx=5)
tk.Entry(seletor, textvariable=ano_atual, width=8, font=("Arial", 11)).pack(side="left", padx=5)
tk.Button(seletor, text="ATUALIZAR", command=atualizar_dashboard,
          bg="#f39c12", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=10)

# ========== CARDS ==========
cards = tk.Frame(root, bg=COR_FUNDO)
cards.pack(fill="x", padx=20, pady=15)

card_rec = tk.Frame(cards, bg=COR_RECEITAS, padx=25, pady=15)
card_rec.pack(side="left", expand=True, fill="both", padx=10)
tk.Label(card_rec, text="TOTAL RECEITAS", font=("Arial", 12, "bold"), bg=COR_RECEITAS, fg="white").pack()
lbl_rec_valor = tk.Label(card_rec, text="R$ 0,00", font=("Arial", 18, "bold"), bg=COR_RECEITAS, fg="white")
lbl_rec_valor.pack()

card_des = tk.Frame(cards, bg=COR_DESPESAS, padx=25, pady=15)
card_des.pack(side="left", expand=True, fill="both", padx=10)
tk.Label(card_des, text="TOTAL DESPESAS", font=("Arial", 12, "bold"), bg=COR_DESPESAS, fg="white").pack()
lbl_des_valor = tk.Label(card_des, text="R$ 0,00", font=("Arial", 18, "bold"), bg=COR_DESPESAS, fg="white")
lbl_des_valor.pack()

card_sal = tk.Frame(cards, bg=COR_SALDO, padx=25, pady=15)
card_sal.pack(side="left", expand=True, fill="both", padx=10)
tk.Label(card_sal, text="SALDO FINAL", font=("Arial", 12, "bold"), bg=COR_SALDO, fg="white").pack()
lbl_saldo_valor = tk.Label(card_sal, text="R$ 0,00", font=("Arial", 18, "bold"), bg=COR_SALDO, fg="white")
lbl_saldo_valor.pack()

# ========== BOTÕES PRINCIPAIS ==========
botoes = tk.Frame(root, bg=COR_FUNDO)
botoes.pack(fill="x", padx=20, pady=5)
tk.Button(botoes, text="💰 LANÇAR RECEITAS", command=janela_cadastrar_receita,
          bg=COR_RECEITAS, fg="white", font=("Arial", 11, "bold"), padx=20, pady=10).pack(side="left", padx=8)
tk.Button(botoes, text="📉 LANÇAR DESPESAS", command=janela_cadastrar_despesa,
          bg=COR_DESPESAS, fg="white", font=("Arial", 11, "bold"), padx=20, pady=10).pack(side="left", padx=8)
tk.Button(botoes, text="📄 GERAR PDF DO MÊS", command=gerar_pdf_mensal,
          bg="#9b59b6", fg="white", font=("Arial", 11, "bold"), padx=20, pady=10).pack(side="left", padx=8)

# ========== RELATÓRIOS POR CATEGORIA — TODOS VISÍVEIS ==========
frame_rel = tk.Frame(root, bg="#e8e4f0", padx=15, pady=15)
frame_rel.pack(fill="x", padx=20, pady=15)

tk.Label(frame_rel, text="📊 RELATÓRIOS POR CATEGORIA — Digite o Ano e clique no botão",
         font=("Arial", 12, "bold"), bg="#e8e4f0", fg=COR_RELATORIO).pack(anchor="w", pady=(0,12))

linha_ano = tk.Frame(frame_rel, bg="#e8e4f0")
linha_ano.pack(anchor="w", pady=(0,12))
tk.Label(linha_ano, text="Ano:", bg="#e8e4f0", font=("Arial", 11, "bold")).pack(side="left", padx=(0,10))
tk.Entry(linha_ano, textvariable=ano_relatorio, width=15, font=("Arial", 12)).pack(side="left")

botoes_rel = tk.Frame(frame_rel, bg="#e8e4f0")
botoes_rel.pack(fill="x")

estilo_normal = {"bg": COR_RELATORIO, "fg": "white", "font": ("Arial", 10, "bold"), "padx": 10, "pady": 10}
estilo_destaque = {"bg": COR_DESTAQUE, "fg": "white", "font": ("Arial", 11, "bold"), "padx": 10, "pady": 12}

# Coluna 1
col1 = tk.Frame(botoes_rel, bg="#e8e4f0")
col1.pack(side="left", fill="both", expand=True, padx=5)

tk.Button(col1, text="💰 1 — SALÁRIO RECEBIDO",
          command=lambda: gerar_relatorio("salario", "SALÁRIO RECEBIDO"),
          **estilo_normal).pack(fill="x", pady=4)

tk.Button(col1, text="💵 2 — ADIANTAMENTO VALE",
          command=lambda: gerar_relatorio("vale", "ADIANTAMENTO VALE RECEBIDO"),
          **estilo_normal).pack(fill="x", pady=4)

tk.Button(col1, text="📄 3 — 13º SALÁRIO 1ª PARCELA",
          command=lambda: gerar_relatorio("decimo1", "13º SALÁRIO — 1ª PARCELA"),
          **estilo_normal).pack(fill="x", pady=4)

tk.Button(col1, text="📄 4 — 13º SALÁRIO 2ª PARCELA",
          command=lambda: gerar_relatorio("decimo2", "13º SALÁRIO — 2ª PARCELA"),
          **estilo_normal).pack(fill="x", pady=4)

# Coluna 2
col2 = tk.Frame(botoes_rel, bg="#e8e4f0")
col2.pack(side="left", fill="both", expand=True, padx=5)

tk.Button(col2, text="🏖️ 5 — SALÁRIO ANTES DAS FÉRIAS",
          command=lambda: gerar_relatorio("salario_antes_ferias", "SALÁRIO ANTES DAS FÉRIAS"),
          **estilo_normal).pack(fill="x", pady=4)

tk.Button(col2, text="🌴 6 — FÉRIAS RECEBIDAS",
          command=lambda: gerar_relatorio("ferias", "FÉRIAS RECEBIDAS"),
          **estilo_normal).pack(fill="x", pady=4)

# ⭐ DESTAQUE — SEMPRE APARECE!
tk.Button(col2, text="⭐ 7 — 10 DIAS TRABALHADOS DAS FÉRIAS ⭐",
          command=lambda: gerar_relatorio("salario_10_dias_trabalhados_ferias", "SALÁRIO REFERENTE AOS 10 DIAS TRABALHADOS DAS FÉRIAS"),
          **estilo_destaque).pack(fill="x", pady=6)

tk.Button(col2, text="💳 8 — VALE APÓS AS FÉRIAS",
          command=lambda: gerar_relatorio("vale_ferias", "VALE APÓS AS FÉRIAS"),
          **estilo_normal).pack(fill="x", pady=4)

# ========== TABELA ==========
lista = tk.Frame(root, bg=COR_FUNDO)
lista.pack(fill="both", expand=True, padx=20, pady=10)
tk.Label(lista, text="LANÇAMENTOS DO MÊS", font=("Arial", 13, "bold"), bg=COR_FUNDO, fg=COR_CABECALHO).pack(anchor="w", pady=(0,10))

tree = ttk.Treeview(lista, columns=("desc", "valor", "tipo"), show="headings", height=6)
tree.heading("desc", text="Descrição")
tree.heading("valor", text="Valor")
tree.heading("tipo", text="Tipo")
tree.column("desc", width=500)
tree.column("valor", width=200)
tree.column("tipo", width=150)
tree.pack(fill="both", expand=True)

atualizar_dashboard()
root.mainloop()