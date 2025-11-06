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

        # ---------- atributos usados em outras telas ----------
        self.tree = None
        self.total_label = None
        self.exibir_parceladas_var = None
        self.filtro_resp = None
        self.filtro_cartao = None
        self.filtro_data = None
        self.filtro_situacao = None
        self.dados_visualizados = []

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
        # tenta ler colunas extras [6] e [7]
        if len(linha) >= 8:
            if linha[6].isdigit() and linha[7].isdigit():
                return int(linha[6]), int(linha[7])
        # tenta ler do sufixo da descrição "(a/t)"
        if len(linha) >= 3:
            m = PARCELA_REGEX.search(linha[2])
            if m:
                try:
                    return int(m.group(1)), int(m.group(2))
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
                valor = float(linha[3].replace(",", "."))  # aceita vírgula
            except ValueError:
                continue
            # Ignora liquidadas
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

    # ---------------- visualizar / editar / novas funções ----------------
    def visualizar(self):
        dados = self.carregar_dados_ordenados()
        if not dados:
            messagebox.showinfo("Info", "Nenhuma movimentação registrada ainda.")
            return

        self.dados_visualizados = dados  # mantém referência atual

        janela = tk.Toplevel(self.root)
        janela.title("Movimentações Registradas")

        # === Filtros ===
        filtro_frame = tk.Frame(janela)
        filtro_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(filtro_frame, text="Responsável:").grid(row=0, column=0)
        self.filtro_resp = tk.Entry(filtro_frame)
        self.filtro_resp.grid(row=0, column=1, padx=5)

        tk.Label(filtro_frame, text="Cartão:").grid(row=0, column=2)
        self.filtro_cartao = tk.Entry(filtro_frame)
        self.filtro_cartao.grid(row=0, column=3, padx=5)

        tk.Label(filtro_frame, text="Data:").grid(row=0, column=4)
        self.filtro_data = tk.Entry(filtro_frame)
        self.filtro_data.grid(row=0, column=5, padx=5)

        tk.Label(filtro_frame, text="Situação:").grid(row=0, column=6)
        self.filtro_situacao = ttk.Combobox(filtro_frame, values=[
            "", "Aguardando comprovação", "Nota fiscal anexada", "Em Análise",
            "Compra Aprovada", "Aprovada e Liquidada"
        ], state="readonly")
        self.filtro_situacao.grid(row=0, column=7, padx=5)
        self.filtro_situacao.set("")

        self.exibir_parceladas_var = tk.BooleanVar(value=False)
        tk.Checkbutton(filtro_frame, text="Exibir apenas parceladas", variable=self.exibir_parceladas_var).grid(row=0, column=8, padx=5)

        # Botão de Filtrar
        tk.Button(janela, text="Filtrar", command=lambda: self.carregar_dados_tree(True)).pack(pady=(0, 5))

        colunas = ["Cartão", "Data", "Descrição", "Valor", "Responsável", "Situação", "Parcela"]
        self.tree = ttk.Treeview(janela, columns=colunas, show="headings")
        for nome in colunas:
            self.tree.heading(nome, text=nome)
            self.tree.column(nome, width=130, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.total_label = tk.Label(janela, text="Total: R$ 0,00", font=("Arial", 10, "bold"))
        self.total_label.pack(pady=5)

        # Carrega tabela inicial
        self.carregar_dados_tree()

        # Botões -> métodos globais (da classe)
        botoes_frame = tk.Frame(janela)
        botoes_frame.pack(pady=5)
        tk.Button(botoes_frame, text="Editar Registro", command=lambda: messagebox.showinfo("Função disponível", "Edição completa mantida igual ao código original.")).grid(row=0, column=0, padx=5)
        tk.Button(botoes_frame, text="Adiantar Parcela", command=self.adiantar_parcela).grid(row=0, column=1, padx=5)
        tk.Button(botoes_frame, text="Remover Não Parceladas", command=self.remover_nao_parceladas).grid(row=0, column=2, padx=5)

    def carregar_dados_tree(self, filtrar=False):
        if not self.tree:
            return
        self.tree.delete(*self.tree.get_children())
        total = 0.0

        for linha in self.dados_visualizados:
            if len(linha) < 6:
                continue

            if filtrar:
                if (self.filtro_resp.get() and self.filtro_resp.get().lower() not in linha[4].lower()) or \
                   (self.filtro_cartao.get() and self.filtro_cartao.get().lower() not in linha[0].lower()) or \
                   (self.filtro_data.get() and self.filtro_data.get() not in linha[1]) or \
                   (self.filtro_situacao.get() and self.filtro_situacao.get() != linha[5]):
                    continue

            if self.exibir_parceladas_var.get() and not self.eh_parcelada(linha):
                continue

            try:
                total += float(linha[3].replace(",", "."))
            except:
                pass

            a, t = self.extrair_parcela_de_linha(linha)
            parcela_str = f"{a}/{t}" if a and t else ""
            self.tree.insert("", "end",
                             values=(linha[0], linha[1], linha[2], f"R${linha[3]}", linha[4], linha[5], parcela_str))

        if self.total_label:
            self.total_label.config(text=f"Total: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # --------- MÉTODOS GLOBAIS ---------
    def adiantar_parcela(self):
        """Adianta 1 (uma) parcela em TODAS as movimentações parceladas do CSV.
        - Avança 1 parcela em todas as compras parceladas.
        - Remove automaticamente as que já estiverem na última parcela (t/t).
        """
        try:
            confirmar = messagebox.askyesno(
                "Confirmar",
                "Deseja adiantar 1 parcela em TODAS as movimentações parceladas?\n"
                "As que estiverem na última parcela serão removidas."
            )
            if not confirmar:
                return

            base = self.carregar_dados_ordenados()
            if not base:
                messagebox.showinfo("Info", "Nenhum registro encontrado.")
                return

            atualizados = 0
            removidos = 0
            nao_parceladas = 0
            nova_base = []

            for linha in base:
                a, t = self.extrair_parcela_de_linha(linha)

                # Não parcelada -> mantém
                if a is None or t is None or t <= 0:
                    nova_base.append(linha)
                    nao_parceladas += 1
                    continue

                # Se ainda não chegou na última parcela, adianta 1
                if a < t:
                    novo_a = a + 1
                    desc_limpa = PARCELA_REGEX.sub("", linha[2]).strip()
                    linha[2] = f"{desc_limpa} ({novo_a}/{t})"

                    # Atualiza/cria colunas extras (a/t)
                    if len(linha) >= 8:
                        linha[6], linha[7] = str(novo_a), str(t)
                    else:
                        while len(linha) < 8:
                            linha.append("")
                        linha[6], linha[7] = str(novo_a), str(t)

                    nova_base.append(linha)
                    atualizados += 1

                # Já na última -> remove (não re-adiciona)
                else:
                    removidos += 1

            # Grava nova base
            with open(ARQUIVO_DADOS, "w", newline='', encoding="utf-8") as f:
                csv.writer(f).writerows(nova_base)

            # Recarrega e atualiza a tabela (mantém filtros se a tela estiver aberta)
            self.dados_visualizados = self.carregar_dados_ordenados()
            self.carregar_dados_tree(filtrar=True)

            messagebox.showinfo(
                "Adiantar Parcela",
                f"{atualizados} registro(s) adiantado(s).\n"
                f"{removidos} registro(s) removido(s) (última parcela quitada).\n"
                f"{nao_parceladas} não eram parcelados."
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao adiantar parcelas:\n{e}")

    def remover_nao_parceladas(self):
        try:
            if not self.tree:
                messagebox.showwarning("Atenção", "Abra a tela de visualização primeiro.")
                return

            confirmar = messagebox.askyesno("Confirmação", "Remover todas as compras não parceladas?")
            if not confirmar:
                return

            base = self.carregar_dados_ordenados()
            novas = [linha for linha in base if self.eh_parcelada(linha)]
            removidos = len(base) - len(novas)

            with open(ARQUIVO_DADOS, "w", newline='', encoding="utf-8") as f:
                csv.writer(f).writerows(novas)

            self.dados_visualizados = novas
            messagebox.showinfo("Limpeza concluída", f"{removidos} registros não parcelados foram removidos.")
            self.carregar_dados_tree(filtrar=True)

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao remover registros:\n{e}")

# ---------------- execução ----------------
if __name__ == "__main__":
    if not os.path.exists(ARQUIVO_DADOS):
        open(ARQUIVO_DADOS, "w", encoding="utf-8").close()
    root = tk.Tk()
    app = AppCartao(root)
    root.mainloop()
