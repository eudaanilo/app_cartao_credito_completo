import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict

ARQUIVO_DADOS = "movimentacoes_cartao.csv"

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

        # Checkbox parcelada
        self.parcelada_var = tk.BooleanVar()
        self.chk_parcelada = tk.Checkbutton(root, text="Compra Parcelada?", variable=self.parcelada_var, command=self.toggle_parcelamento)
        self.chk_parcelada.grid(row=linha_atual, column=0, columnspan=2, sticky="w", padx=5, pady=3)

        # Entradas de parcelas
        tk.Label(root, text="Parcela Atual").grid(row=linha_atual+1, column=0, sticky="w", padx=5)
        self.parcela_atual_entry = tk.Entry(root, state="disabled")
        self.parcela_atual_entry.grid(row=linha_atual+1, column=1, sticky="ew", padx=5)

        tk.Label(root, text="Total de Parcelas").grid(row=linha_atual+2, column=0, sticky="w", padx=5)
        self.total_parcelas_entry = tk.Entry(root, state="disabled")
        self.total_parcelas_entry.grid(row=linha_atual+2, column=1, sticky="ew", padx=5)

        # Botões principais
        tk.Button(root, text="Salvar Movimentação", command=self.salvar).grid(row=linha_atual+3, column=0, columnspan=2, pady=10)
        tk.Button(root, text="Visualizar Registros", command=self.visualizar).grid(row=linha_atual+4, column=0, columnspan=2)

        # AQUI É O LUGAR CERTO para adicionar o botão de gráficos
        tk.Button(root, text="Mostrar Gráficos", command=self.mostrar_grafico).grid(row=linha_atual+5, column=0, columnspan=2, pady=10)


    def mostrar_grafico(self):
        try:
            with open(ARQUIVO_DADOS, newline='', encoding="utf-8") as f:
                reader = csv.reader(f)
                dados = list(reader)
        except FileNotFoundError:
            messagebox.showerror("Erro", "Nenhuma movimentação registrada ainda.")
            return

        if not dados:
            messagebox.showinfo("Info", "Nenhum registro para gerar gráfico.")
            return

        # Agrupar valores por responsável
        total_por_responsavel = defaultdict(float)
        total_por_cartao = defaultdict(float)
        for linha in dados:
            if len(linha) != 6:
                continue
            valor = 0.0
            try:
                valor = float(linha[3].replace(",", "."))
            except ValueError:
                continue
            situacao = linha[5]
            if situacao == "Aprovada e Liquidada":
                continue  # Ignorar no gráfico de total
            total_por_responsavel[linha[4]] += valor
            total_por_cartao[linha[0]] += valor

        # Criar janela do gráfico
        graf_win = tk.Toplevel(self.root)
        graf_win.title("Gráficos de Gastos")

        fig, axs = plt.subplots(1, 2, figsize=(10,4))

        # Gráfico por responsável
        axs[0].bar(total_por_responsavel.keys(), total_por_responsavel.values(), color='skyblue')
        axs[0].set_title("Gastos por Responsável")
        axs[0].set_ylabel("R$")
        axs[0].tick_params(axis='x', rotation=45)

        # Gráfico por cartão
        axs[1].bar(total_por_cartao.keys(), total_por_cartao.values(), color='lightgreen')
        axs[1].set_title("Gastos por Cartão")
        axs[1].set_ylabel("R$")
        axs[1].tick_params(axis='x', rotation=45)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=graf_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def toggle_parcelamento(self):
        estado = "normal" if self.parcelada_var.get() else "disabled"
        self.parcela_atual_entry.configure(state=estado)
        self.total_parcelas_entry.configure(state=estado)

    def salvar(self):
        campos_ordem = ["cartao", "data", "descricao", "valor", "responsavel", "situacao"]
        dados = {k: self.entradas[k].get() for k in campos_ordem}

        if not all(dados.values()):
            messagebox.showwarning("Campos incompletos", "Por favor, preencha todos os campos.")
            return

        try:
            datetime.strptime(dados['data'], "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Data inválida", "A data deve estar no formato dd/mm/aaaa.")
            return

        if self.parcelada_var.get():
            atual = self.parcela_atual_entry.get()
            total = self.total_parcelas_entry.get()
            if not atual.isdigit() or not total.isdigit():
                messagebox.showerror("Erro nas parcelas", "Informe valores numéricos válidos para as parcelas.")
                return
            dados["descricao"] += f" ({atual}/{total})"

        with open(ARQUIVO_DADOS, "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([dados[k] for k in campos_ordem])

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

    def visualizar(self):
        try:
            with open(ARQUIVO_DADOS, newline='', encoding="utf-8") as f:
                reader = csv.reader(f)
                dados = list(reader)
        except FileNotFoundError:
            messagebox.showerror("Erro", "Nenhuma movimentação registrada ainda.")
            return

        janela = tk.Toplevel(self.root)
        janela.title("Movimentações Registradas")

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
            "", "Aguardando comprovação", "Nota fiscal anexada", 
            "Em Análise", "Compra Aprovada", "Aprovada e Liquidada"
        ], state="readonly")
        filtro_situacao.grid(row=0, column=7, padx=5)
        filtro_situacao.set("")

        colunas = ["Cartão", "Data", "Descrição", "Valor", "Responsável", "Situação"]
        tree = ttk.Treeview(janela, columns=colunas, show="headings")
        for nome in colunas:
            tree.heading(nome, text=nome)
            tree.column(nome, width=130, anchor="center")

        total_label = tk.Label(janela, text="Total: R$ 0,00", font=("Arial", 10, "bold"))
        total_label.pack(pady=5)

        def carregar_dados(filtrar=False):
            tree.delete(*tree.get_children())
            total = 0.0
            for linha in dados:
                if len(linha) != 6:
                    continue
                if filtrar:
                    if (filtro_resp.get() and filtro_resp.get().lower() not in linha[4].lower()) or \
                       (filtro_cartao.get() and filtro_cartao.get().lower() not in linha[0].lower()) or \
                       (filtro_data.get() and filtro_data.get() not in linha[1]) or \
                       (filtro_situacao.get() and filtro_situacao.get() != linha[5]):
                        continue
                # Somar apenas se não for "Aprovada e Liquidada" ou se o filtro estiver selecionado
                if linha[5] != "Aprovada e Liquidada" or filtro_situacao.get() == "Aprovada e Liquidada":
                    try:
                        total += float(linha[3].replace(",", "."))
                    except ValueError:
                        pass
                valor_formatado = f"R${linha[3]}"
                tree.insert("", "end", values=(linha[0], linha[1], linha[2], valor_formatado, linha[4], linha[5]))
            
            total_label.config(text=f"Total: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        carregar_dados()
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Button(janela, text="Filtrar", command=lambda: carregar_dados(True)).pack(pady=5)

        def editar_registro():
            selecionado = tree.selection()
            if not selecionado:
                messagebox.showwarning("Atenção", "Selecione um registro para editar.")
                return
            indice = tree.index(selecionado)
            valores = tree.item(selecionado)["values"]

            edit_win = tk.Toplevel(janela)
            edit_win.title("Editar Registro")
            entradas_edit = {}
            campos = ["Cartão", "Data", "Descrição", "Valor", "Responsável", "Situação"]

            for i, campo in enumerate(campos):
                tk.Label(edit_win, text=campo).grid(row=i, column=0, sticky="w", padx=5, pady=3)
                entrada = ttk.Combobox(edit_win, state="readonly", values=[
                    "Aguardando comprovação", 
                    "Nota fiscal anexada",
                    "Em Análise",
                    "Compra Aprovada",
                    "Aprovada e Liquidada"
                ]) if campo == "Situação" else tk.Entry(edit_win)
                entrada.grid(row=i, column=1, padx=5, pady=3, sticky="ew")
                entrada.insert(0, valores[i].replace("R$", "") if campo == "Valor" else valores[i])
                entradas_edit[campo] = entrada

            def salvar_edicao():
                novos = [entradas_edit[c].get() for c in campos]
                dados[indice] = novos
                with open(ARQUIVO_DADOS, "w", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerows(dados)
                edit_win.destroy()
                janela.destroy()
                self.visualizar()

            def excluir_registro():
                confirmar = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este registro?")
                if confirmar:
                    dados.pop(indice)
                    with open(ARQUIVO_DADOS, "w", newline='', encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerows(dados)
                    edit_win.destroy()
                    janela.destroy()
                    self.visualizar()

            tk.Button(edit_win, text="Salvar Alterações", command=salvar_edicao).grid(row=6, column=0, pady=10, padx=5, sticky="ew")
            tk.Button(edit_win, text="Excluir Registro", command=excluir_registro).grid(row=6, column=1, pady=10, padx=5, sticky="ew")


        tk.Button(janela, text="Editar Registro", command=editar_registro).pack(pady=5)

        tk.Button(root, text="Mostrar Gráficos", command=self.mostrar_grafico).grid(row=linha_atual+5, column=0, columnspan=2, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppCartao(root)
    root.mainloop()
