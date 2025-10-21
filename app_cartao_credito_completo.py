import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import re
import os

ARQUIVO_DADOS = "movimentacoes_cartao.csv"
PARCELA_REGEX = re.compile(r"\((\d+)\s*/\s*(\d+)\)")

class AppCartao:
    def __init__(self, root):
        self.root = root
        self.root.title("Protocolo de Movimentação – Cartão de Crédito")

        campos = [
            ("Cartão Utilizado", "cartao"),
            ("Data da Compra (dd/mm/aaaa)", "data"),
            ("Descrição da Compra", "descricao"),
            ("Valor da Compra (R$)", "valor"),
            ("Responsável pela Compra", "responsavel"),
            ("Situação da Movimentação", "situacao"),
        ]

        self.entradas = {}
        for i, (label_text, key) in enumerate(campos):
            tk.Label(root, text=label_text).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            if key == "situacao":
                cb = ttk.Combobox(root, values=[
                    "Aguardando comprovação",
                    "Nota fiscal anexada",
                    "Em Análise",
                    "Compra Aprovada",
                    "Aprovada e Liquidada"
                ], state="readonly")
                cb.grid(row=i, column=1, padx=5, pady=3, sticky="ew")
                self.entradas[key] = cb
            else:
                e = tk.Entry(root)
                e.grid(row=i, column=1, padx=5, pady=3, sticky="ew")
                self.entradas[key] = e

        linha_atual = len(campos)
        self.parcelada_var = tk.BooleanVar()
        self.chk_parcelada = tk.Checkbutton(root, text="Compra Parcelada?", variable=self.parcelada_var, command=self.toggle_parcelamento)
        self.chk_parcelada.grid(row=linha_atual, column=0, columnspan=2, sticky="w", padx=5, pady=3)

        tk.Label(root, text="Parcela Atual").grid(row=linha_atual+1, column=0, sticky="w", padx=5)
        self.parcela_atual_entry = tk.Entry(root, state="disabled")
        self.parcela_atual_entry.grid(row=linha_atual+1, column=1, sticky="ew", padx=5)

        tk.Label(root, text="Total de Parcelas").grid(row=linha_atual+2, column=0, sticky="w", padx=5)
        self.total_parcelas_entry = tk.Entry(root, state="disabled")
        self.total_parcelas_entry.grid(row=linha_atual+2, column=1, sticky="ew", padx=5)

        tk.Button(root, text="Salvar Movimentação", command=self.salvar).grid(row=linha_atual+3, column=0, columnspan=2, pady=10)
        tk.Button(root, text="Visualizar Registros", command=self.visualizar).grid(row=linha_atual+4, column=0, columnspan=2)
        tk.Button(root, text="Mostrar Gráficos", command=self.mostrar_grafico).grid(row=linha_atual+5, column=0, columnspan=2, pady=10)

    # ---------------- utilitários ----------------
    def extrair_parcela_de_linha(self, linha):
        atual = None
        total = None
        if len(linha) >= 8:
            if linha[6].isdigit() and linha[7].isdigit():
                try:
                    atual = int(linha[6])
                    total = int(linha[7])
                    return atual, total
                except:
                    pass
        if len(linha) >= 3:
            m = PARCELA_REGEX.search(linha[2])
            if m:
                try:
                    atual = int(m.group(1))
                    total = int(m.group(2))
                    return atual, total
                except:
                    pass
        return None, None

    def eh_parcelada(self, linha):
        a, t = self.extrair_parcela_de_linha(linha)
        return (a is not None and t is not None and t > 0)

    # ---------------- salvar ----------------
    def salvar(self):
        campos_ordem = ["cartao", "data", "descricao", "valor", "responsavel", "situacao"]
        dados_form = {k: self.entradas[k].get() for k in campos_ordem}

        if not all(dados_form.values()):
            messagebox.showwarning("Campos incompletos", "Por favor, preencha todos os campos.")
            return

        try:
            datetime.strptime(dados_form['data'], "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Data inválida", "A data deve estar no formato dd/mm/aaaa.")
            return

        linha_para_gravar = [dados_form[k] for k in campos_ordem]

        if self.parcelada_var.get():
            atual = self.parcela_atual_entry.get()
            total = self.total_parcelas_entry.get()
            if not atual.isdigit() or not total.isdigit():
                messagebox.showerror("Erro nas parcelas", "Informe valores numéricos válidos para as parcelas.")
                return
            descricao = linha_para_gravar[2]
            descricao = PARCELA_REGEX.sub("", descricao).strip()
            descricao = f"{descricao} ({int(atual)}/{int(total)})"
            linha_para_gravar[2] = descricao
            linha_para_gravar.append(str(int(atual)))
            linha_para_gravar.append(str(int(total)))

        with open(ARQUIVO_DADOS, "a", newline='', encoding="utf-8") as f:
            csv.writer(f).writerow(linha_para_gravar)

        messagebox.showinfo("Sucesso", "Movimentação salva com sucesso.")
        for e in self.entradas.values():
            if isinstance(e, tk.Entry):
                e.delete(0, tk.END)
            elif isinstance(e, ttk.Combobox):
                e.set("")
        self.parcelada_var.set(False)
        self.parcela_atual_entry.configure(state="disabled")
        self.total_parcelas_entry.configure(state="disabled")
        self.parcela_atual_entry.delete(0, tk.END)
        self.total_parcelas_entry.delete(0, tk.END)

    def toggle_parcelamento(self):
        estado = "normal" if self.parcelada_var.get() else "disabled"
        self.parcela_atual_entry.configure(state=estado)
        self.total_parcelas_entry.configure(state=estado)

    # ---------------- carregar / gráficos ----------------
    def carregar_dados_ordenados(self):
        try:
            with open(ARQUIVO_DADOS, newline='', encoding="utf-8") as f:
                dados = list(csv.reader(f))
        except FileNotFoundError:
            return []
        def data_valida(linha):
            try:
                return datetime.strptime(linha[1], "%d/%m/%Y")
            except:
                return datetime.min
        dados.sort(key=data_valida)
        return dados

    def mostrar_grafico(self):
        try:
            with open(ARQUIVO_DADOS, newline='', encoding="utf-8") as f:
                dados = list(csv.reader(f))
        except FileNotFoundError:
            messagebox.showerror("Erro", "Nenhuma movimentação registrada ainda.")
            return
        if not dados:
            messagebox.showinfo("Info", "Nenhum registro para gerar gráfico.")
            return

        total_por_responsavel = defaultdict(float)
        total_por_cartao = defaultdict(float)
        for linha in dados:
            if len(linha) < 4:
                continue
            try:
                valor = float(linha[3].replace(",", "."))
            except ValueError:
                continue
            if len(linha) > 5 and linha[5] == "Aprovada e Liquidada":
                continue
            total_por_responsavel[linha[4]] += valor
            total_por_cartao[linha[0]] += valor

        graf_win = tk.Toplevel(self.root)
        graf_win.title("Gráficos de Gastos")

        fig, axs = plt.subplots(1, 2, figsize=(10,4))
        axs[0].bar(total_por_responsavel.keys(), total_por_responsavel.values())
        axs[0].set_title("Gastos por Responsável")
        axs[0].tick_params(axis='x', rotation=45)

        axs[1].bar(total_por_cartao.keys(), total_por_cartao.values())
        axs[1].set_title("Gastos por Cartão")
        axs[1].tick_params(axis='x', rotation=45)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=graf_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---------------- visualizar / editar ----------------
    def visualizar(self):
        dados = self.carregar_dados_ordenados()
        if not dados:
            messagebox.showinfo("Info", "Nenhuma movimentação registrada ainda.")
            return

        janela = tk.Toplevel(self.root)
        janela.title("Movimentações Registradas")

        # === Filtros ===
        filtro_frame = tk.Frame(janela)
        filtro_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(filtro_frame, text="Responsável:").grid(row=0, column=0)
        filtro_resp = tk.Entry(filtro_frame)
        filtro_resp.grid(row=0, column=1, padx=5)
        tk.Label(filtro_frame, text="Cartão:").grid(row=0, column=2)
        filtro_cartao = tk.Entry(filtro_frame)
        filtro_cartao.grid(row=0, column=3, padx=5)
        tk.Label(filtro_frame, text="Data:").grid(row=0, column=4)
        filtro_data = tk.Entry(filtro_frame)
        filtro_data.grid(row=0, column=5, padx=5)
        tk.Label(filtro_frame, text="Situação:").grid(row=0, column=6)
        filtro_situacao = ttk.Combobox(filtro_frame, values=[
            "", "Aguardando comprovação", "Nota fiscal anexada", "Em Análise",
            "Compra Aprovada", "Aprovada e Liquidada"
        ], state="readonly")
        filtro_situacao.grid(row=0, column=7, padx=5)
        filtro_situacao.set("")
        exibir_parceladas_var = tk.BooleanVar(value=False)
        tk.Checkbutton(filtro_frame, text="Exibir apenas parceladas", variable=exibir_parceladas_var).grid(row=0, column=8, padx=5)

        colunas = ["Cartão", "Data", "Descrição", "Valor", "Responsável", "Situação", "Parcela"]
        tree = ttk.Treeview(janela, columns=colunas, show="headings")
        for nome in colunas:
            tree.heading(nome, text=nome)
            tree.column(nome, width=130, anchor="center")
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        total_label = tk.Label(janela, text="Total: R$ 0,00", font=("Arial", 10, "bold"))
        total_label.pack(pady=5)

        def carregar_dados_tree(filtrar=False):
            tree.delete(*tree.get_children())
            total = 0.0
            for linha in dados:
                if len(linha) < 6:
                    continue
                if filtrar:
                    if (filtro_resp.get() and filtro_resp.get().lower() not in linha[4].lower()) or \
                       (filtro_cartao.get() and filtro_cartao.get().lower() not in linha[0].lower()) or \
                       (filtro_data.get() and filtro_data.get() not in linha[1]) or \
                       (filtro_situacao.get() and filtro_situacao.get() != linha[5]):
                        continue
                if exibir_parceladas_var.get() and not self.eh_parcelada(linha):
                    continue
                try:
                    total += float(linha[3].replace(",", "."))
                except:
                    pass
                a, t = self.extrair_parcela_de_linha(linha)
                parcela_str = f"{a}/{t}" if a and t else ""
                tree.insert("", "end", values=(linha[0], linha[1], linha[2], f"R${linha[3]}", linha[4], linha[5], parcela_str))
            total_label.config(text=f"Total: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        carregar_dados_tree()
        tk.Button(janela, text="Filtrar", command=lambda: carregar_dados_tree(True)).pack(pady=5)

        # === Botão editar ===
        def editar_registro():
            selecionado = tree.selection()
            if not selecionado:
                messagebox.showwarning("Atenção", "Selecione um registro para editar.")
                return
            valores = tree.item(selecionado)["values"]
            alvo_cartao, alvo_data, alvo_desc, alvo_valor, alvo_resp, alvo_sit = valores[:6]
            indice = None
            for i, linha in enumerate(dados):
                if len(linha) >= 6 and linha[0] == alvo_cartao and linha[1] == alvo_data and linha[2] == alvo_desc and (f"R${linha[3]}" == alvo_valor or linha[3] == alvo_valor) and linha[4] == alvo_resp and linha[5] == alvo_sit:
                    indice = i
                    break
            if indice is None:
                messagebox.showerror("Erro", "Registro não pôde ser localizado para edição.")
                return

            valores_linha = dados[indice]
            edit_win = tk.Toplevel(janela)
            edit_win.title("Editar Registro")
            entradas_edit = {}

            campos = ["Cartão", "Data", "Descrição", "Valor", "Responsável", "Situação", "Parcela Atual", "Total Parcelas"]
            for i, campo in enumerate(campos):
                tk.Label(edit_win, text=campo).grid(row=i, column=0, sticky="w", padx=5, pady=3)
                entrada = ttk.Combobox(edit_win, state="readonly", values=[
                    "Aguardando comprovação", "Nota fiscal anexada", "Em Análise",
                    "Compra Aprovada", "Aprovada e Liquidada"
                ]) if campo == "Situação" else tk.Entry(edit_win)
                entrada.grid(row=i, column=1, padx=5, pady=3, sticky="ew")
                if campo == "Parcela Atual":
                    a, t = self.extrair_parcela_de_linha(valores_linha)
                    entrada.insert(0, str(a) if a else "")
                elif campo == "Total Parcelas":
                    a, t = self.extrair_parcela_de_linha(valores_linha)
                    entrada.insert(0, str(t) if t else "")
                else:
                    mapping = {"Cartão":0, "Data":1, "Descrição":2, "Valor":3, "Responsável":4, "Situação":5}
                    entrada.insert(0, valores_linha[mapping[campo]] if campo in mapping else "")
                entradas_edit[campo] = entrada

            def salvar_edicao():
                nonlocal dados
                novos = [
                    entradas_edit["Cartão"].get(),
                    entradas_edit["Data"].get(),
                    entradas_edit["Descrição"].get(),
                    entradas_edit["Valor"].get(),
                    entradas_edit["Responsável"].get(),
                    entradas_edit["Situação"].get()
                ]
                parcela_atual = entradas_edit["Parcela Atual"].get().strip()
                total_parcelas = entradas_edit["Total Parcelas"].get().strip()
                if parcela_atual.isdigit() and total_parcelas.isdigit():
                    novos.append(parcela_atual)
                    novos.append(total_parcelas)
                    desc = PARCELA_REGEX.sub("", novos[2]).strip()
                    novos[2] = f"{desc} ({parcela_atual}/{total_parcelas})"

                dados[indice] = novos
                with open(ARQUIVO_DADOS, "w", newline='', encoding="utf-8") as f:
                    csv.writer(f).writerows(dados)
                messagebox.showinfo("Sucesso", "Registro atualizado com sucesso.")
                edit_win.destroy()
                janela.destroy()
                self.visualizar()

            def excluir_registro():
                nonlocal dados
                confirmar = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este registro?")
                if confirmar:
                    dados.pop(indice)
                    with open(ARQUIVO_DADOS, "w", newline='', encoding="utf-8") as f:
                        csv.writer(f).writerows(dados)
                    messagebox.showinfo("Sucesso", "Registro excluído com sucesso.")
                    edit_win.destroy()
                    janela.destroy()
                    self.visualizar()

            tk.Button(edit_win, text="Salvar Alterações", command=salvar_edicao).grid(row=9, column=0, pady=10, padx=5, sticky="ew")
            tk.Button(edit_win, text="Excluir Registro", command=excluir_registro).grid(row=9, column=1, pady=10, padx=5, sticky="ew")

        tk.Button(janela, text="Editar Registro", command=editar_registro).pack(pady=5)

# ---------------- execução ----------------
if __name__ == "__main__":
    if not os.path.exists(ARQUIVO_DADOS):
        open(ARQUIVO_DADOS, "w", encoding="utf-8").close()
    root = tk.Tk()
    app = AppCartao(root)
    root.mainloop()
