
import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import datetime

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
                    "Compra indevida – aguardando regularização",
                    "Compra Aprovada",
                    "Em disputa / contestação no banco"
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
        root.grid_columnconfigure(1, weight=1)

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

        colunas = ["Cartão", "Data", "Descrição", "Valor", "Responsável", "Situação"]
        tree = ttk.Treeview(janela, columns=colunas, show="headings")
        for nome in colunas:
            tree.heading(nome, text=nome)
            tree.column(nome, width=130, anchor="center")

        def carregar_dados(filtrar=False):
            tree.delete(*tree.get_children())
            for linha in dados:
                if len(linha) == 6:
                    if filtrar:
                        if (filtro_resp.get() and filtro_resp.get().lower() not in linha[4].lower()) or                            (filtro_cartao.get() and filtro_cartao.get().lower() not in linha[0].lower()) or                            (filtro_data.get() and filtro_data.get() not in linha[1]):
                            continue
                    valor_formatado = f"R${linha[3]}"
                    tree.insert("", "end", values=(linha[0], linha[1], linha[2], valor_formatado, linha[4], linha[5]))

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
                    "Compra indevida – aguardando regularização",
                    "Compra Aprovada",
                    "Em disputa / contestação no banco"
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

            tk.Button(edit_win, text="Salvar Alterações", command=salvar_edicao).grid(row=6, columnspan=2, pady=10)

        tk.Button(janela, text="Editar Registro", command=editar_registro).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppCartao(root)
    root.mainloop()
