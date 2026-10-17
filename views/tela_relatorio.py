"""
views/tela_relatorio.py
-----------------------
Tela de relatório e fechamento por período com exportação PDF via ReportLab.
"""

import os
import tempfile
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

# Imports do ReportLab para PDF nativo
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class TelaRelatorio(ctk.CTkToplevel):
    def __init__(self, parent, banco):
        super().__init__(parent)
        self.banco = banco

        self.title("Relatório de Vendas / Fechamento por Período")
        self.geometry("780x680")
        self.minsize(700, 520)

        self.grab_set()

        self._montar_layout()
        self._carregar_dados_padrao()

    def _montar_layout(self):
        # Título
        lbl_titulo = ctk.CTkLabel(
            self, 
            text="RELATÓRIO DE VENDAS POR PERÍODO", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        lbl_titulo.pack(pady=(15, 5))

        # Filtro de Período (De / Até)
        frame_filtro = ctk.CTkFrame(self, fg_color="transparent")
        frame_filtro.pack(pady=10)

        ctk.CTkLabel(frame_filtro, text="De (Data Inicial):", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 4))
        self.entry_inicio = ctk.CTkEntry(frame_filtro, width=110, font=ctk.CTkFont(size=13), placeholder_text="DD/MM/AAAA")
        self.entry_inicio.pack(side="left", padx=4)
        self.entry_inicio.bind("<FocusOut>", lambda evento: self._normalizar_data_digitada(self.entry_inicio))

        ctk.CTkLabel(frame_filtro, text="Até (Data Final):", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(10, 4))
        self.entry_fim = ctk.CTkEntry(frame_filtro, width=110, font=ctk.CTkFont(size=13), placeholder_text="DD/MM/AAAA")
        self.entry_fim.pack(side="left", padx=4)
        self.entry_fim.bind("<FocusOut>", lambda evento: self._normalizar_data_digitada(self.entry_fim))

        btn_buscar = ctk.CTkButton(
            frame_filtro, 
            text="🔍 Filtrar", 
            width=90, 
            command=self._filtrar
        )
        btn_buscar.pack(side="left", padx=8)

        btn_pdf = ctk.CTkButton(
            frame_filtro, 
            text="📄 Gerar PDF", 
            width=110,
            fg_color="#2FA572",
            hover_color="#1E7E53",
            command=self._gerar_pdf
        )
        btn_pdf.pack(side="left", padx=4)

        # Painel de Resumo KPI
        self.frame_resumo = ctk.CTkFrame(self, corner_radius=10)
        self.frame_resumo.pack(fill="x", padx=20, pady=8)

        self.lbl_total_pedidos = ctk.CTkLabel(
            self.frame_resumo, 
            text="Total de Pedidos: 0", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.lbl_total_pedidos.pack(side="left", padx=20, pady=12)

        self.lbl_faturamento = ctk.CTkLabel(
            self.frame_resumo, 
            text="Faturamento: R$ 0,00", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#2FA572"
        )
        self.lbl_faturamento.pack(side="right", padx=20, pady=12)

        # Seção de Pagamentos
        ctk.CTkLabel(self, text="--- Resumo por Formas de Pagamento ---", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(pady=(5, 2))

        self.frame_pagamentos = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_pagamentos.pack(fill="x", padx=20, pady=2)

        # Seção de Listagem dos Pedidos
        ctk.CTkLabel(self, text="--- Lista de Pedidos Encontrados ---", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(pady=(8, 2))

        self.scroll_pedidos = ctk.CTkScrollableFrame(self, height=250)
        self.scroll_pedidos.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _carregar_dados_padrao(self):
        hoje = datetime.now().strftime("%d/%m/%Y")
        self.entry_inicio.delete(0, "end")
        self.entry_inicio.insert(0, hoje)
        self.entry_fim.delete(0, "end")
        self.entry_fim.insert(0, hoje)
        self._filtrar()

    def _normalizar_data_digitada(self, entry):
        """
        Deixa o campo de data no formato DD/MM/AAAA automaticamente,
        mesmo se o usuario digitar so os numeros (ex: "050826" vira
        "05/08/2026").

        Regras:
            8 digitos (ex: 05082026) -> DD/MM/AAAA direto
            6 digitos (ex: 050826)   -> DD/MM/20AA (assume ano 20xx)
            outros casos             -> deixa como esta
        """
        texto = entry.get().strip()
        apenas_digitos = "".join(filter(str.isdigit, texto))

        if len(apenas_digitos) == 8:
            formatado = f"{apenas_digitos[0:2]}/{apenas_digitos[2:4]}/{apenas_digitos[4:8]}"
        elif len(apenas_digitos) == 6:
            formatado = f"{apenas_digitos[0:2]}/{apenas_digitos[2:4]}/20{apenas_digitos[4:6]}"
        else:
            return  # formato nao reconhecido - deixa como o usuario digitou

        entry.delete(0, "end")
        entry.insert(0, formatado)

    def _filtrar(self):
        # Garante que a data digitada (com ou sem barras) esteja
        # normalizada antes de usar, mesmo que o usuario nao tenha
        # saido do campo (ex: clicou direto em "Filtrar").
        self._normalizar_data_digitada(self.entry_inicio)
        self._normalizar_data_digitada(self.entry_fim)

        d_inicio = self.entry_inicio.get().strip()
        d_fim = self.entry_fim.get().strip() or d_inicio

        if not d_inicio:
            messagebox.showwarning("Aviso", "Por favor, digite pelo menos a data inicial.")
            return

        self.dados_atuais = self.banco.gerar_relatorio(d_inicio, d_fim)

        # Atualiza Totais
        self.lbl_total_pedidos.configure(text=f"Total de Pedidos: {self.dados_atuais['qtd_pedidos']}")
        self.lbl_faturamento.configure(text=f"Faturamento Total: R$ {self.dados_atuais['total_vendas']:.2f}".replace('.', ','))

        # Limpa e reconstrói as formas de pagamento
        for child in self.frame_pagamentos.winfo_children():
            child.destroy()

        if self.dados_atuais["detalhe_pagamento"]:
            for forma, valor in self.dados_atuais["detalhe_pagamento"].items():
                lbl_item = ctk.CTkLabel(
                    self.frame_pagamentos,
                    text=f"• {forma}: R$ {valor:.2f}".replace('.', ','),
                    font=ctk.CTkFont(size=13, weight="bold")
                )
                lbl_item.pack(side="left", padx=12, pady=2)
        else:
            ctk.CTkLabel(self.frame_pagamentos, text="Nenhum pagamento registrado no período.", text_color="gray").pack()

        # Limpa e reconstrói a lista de pedidos
        for child in self.scroll_pedidos.winfo_children():
            child.destroy()

        if not self.dados_atuais["pedidos"]:
            ctk.CTkLabel(self.scroll_pedidos, text="Nenhum pedido encontrado para estas datas.", font=ctk.CTkFont(size=14)).pack(pady=20)
            return

        for p in self.dados_atuais["pedidos"]:
            f_item = ctk.CTkFrame(self.scroll_pedidos)
            f_item.pack(fill="x", pady=3, padx=5)

            txt_info = f"#{p.numero_pedido} | {p.data} às {p.hora} | Cliente: {p.cliente} | {p.pagamento} | R$ {p.valor:.2f}".replace('.', ',')
            ctk.CTkLabel(f_item, text=txt_info, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(4, 0))

            txt_detalhe = f"Itens: {p.produto} | Endereço: {p.endereco}"
            if p.observacao:
                txt_detalhe += f" | Obs: {p.observacao}"
            ctk.CTkLabel(f_item, text=txt_detalhe, font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=10, pady=(0, 4))

    def _gerar_pdf(self):
        if not hasattr(self, 'dados_atuais') or not self.dados_atuais["pedidos"]:
            messagebox.showwarning("Aviso", "Não há pedidos no período selecionado para gerar o PDF.")
            return

        # Gera em uma pasta temporaria (nao na Área de Trabalho), pois o
        # objetivo agora e so abrir para o usuario ver na tela - se ele
        # quiser guardar de verdade, escolhe "Salvar como" no proprio
        # visualizador de PDF que abrir.
        nome_arquivo = f"Relatorio_Vendas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        caminho_salvar = os.path.join(tempfile.gettempdir(), nome_arquivo)

        try:
            doc = SimpleDocTemplate(
                caminho_salvar,
                pagesize=A4,
                leftMargin=30,
                rightMargin=30,
                topMargin=30,
                bottomMargin=30
            )

            styles = getSampleStyleSheet()
            
            # Estilos Customizados
            style_title = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=18,
                textColor=colors.HexColor('#1A365D'),
                spaceAfter=4
            )

            style_subtitle = ParagraphStyle(
                'DocSubTitle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                textColor=colors.HexColor('#4A5568'),
                spaceAfter=15
            )

            style_section = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=12,
                textColor=colors.HexColor('#2B6CB0'),
                spaceBefore=12,
                spaceAfter=6
            )

            style_cell = ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=8.5,
                leading=11
            )

            style_cell_bold = ParagraphStyle(
                'TableCellBold',
                parent=style_cell,
                fontName='Helvetica-Bold'
            )

            # Estilos específicos para o card de KPI (sem sobreposição)
            style_kpi_title = ParagraphStyle(
                'KPITitle',
                parent=style_cell,
                fontName='Helvetica-Bold',
                fontSize=8,
                leading=10,
                textColor=colors.HexColor('#4A5568'),
                alignment=1 # Centralizado
            )

            style_kpi_val = ParagraphStyle(
                'KPIVal',
                parent=style_cell,
                fontName='Helvetica-Bold',
                fontSize=14,
                leading=18,
                textColor=colors.HexColor('#1A365D'),
                alignment=1
            )

            style_kpi_val_green = ParagraphStyle(
                'KPIValGreen',
                parent=style_kpi_val,
                textColor=colors.HexColor('#2F855A')
            )

            elements = []

            # Cabeçalho
            elements.append(Paragraph("DELIVERY CONTROL - RELATÓRIO DE VENDAS", style_title))
            meta_txt = f"<b>Período:</b> {self.dados_atuais['data_inicio']} até {self.dados_atuais['data_fim']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Emitido em:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
            elements.append(Paragraph(meta_txt, style_subtitle))
            elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceAfter=12))

            # Cards de Resumo (Divisão em 2 linhas para garantir alinhamento perfeito)
            ticket_medio = (self.dados_atuais['total_vendas'] / self.dados_atuais['qtd_pedidos']) if self.dados_atuais['qtd_pedidos'] > 0 else 0
            kpi_data = [
                [
                    Paragraph("TOTAL DE PEDIDOS", style_kpi_title),
                    Paragraph("TICKET MÉDIO", style_kpi_title),
                    Paragraph("FATURAMENTO TOTAL", style_kpi_title)
                ],
                [
                    Paragraph(f"{self.dados_atuais['qtd_pedidos']}", style_kpi_val),
                    Paragraph(f"R$ {ticket_medio:.2f}".replace('.', ','), style_kpi_val),
                    Paragraph(f"R$ {self.dados_atuais['total_vendas']:.2f}".replace('.', ','), style_kpi_val_green)
                ]
            ]
            t_kpi = Table(kpi_data, colWidths=[175, 175, 185])
            t_kpi.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,0), 6),
                ('BOTTOMPADDING', (0,0), (-1,0), 2),
                ('TOPPADDING', (0,1), (-1,1), 2),
                ('BOTTOMPADDING', (0,1), (-1,1), 8),
            ]))
            elements.append(t_kpi)
            elements.append(Spacer(1, 10))

            # Tabela de Formas de Pagamento
            elements.append(Paragraph("Resumo por Formas de Pagamento", style_section))
            pag_data = [[
                Paragraph("Forma de Pagamento", style_cell_bold),
                Paragraph("Valor Acumulado", style_cell_bold),
                Paragraph("% Participação", style_cell_bold)
            ]]

            for forma, valor in self.dados_atuais["detalhe_pagamento"].items():
                pct = (valor / self.dados_atuais["total_vendas"] * 100) if self.dados_atuais["total_vendas"] > 0 else 0
                pag_data.append([
                    Paragraph(forma, style_cell),
                    Paragraph(f"R$ {valor:.2f}".replace('.', ','), style_cell),
                    Paragraph(f"{pct:.1f}%".replace('.', ','), style_cell)
                ])

            t_pag = Table(pag_data, colWidths=[235, 150, 150])
            t_pag.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ]))
            elements.append(t_pag)
            elements.append(Spacer(1, 10))

            # Tabela Detalhada de Pedidos
            elements.append(Paragraph("Detalhamento de Pedidos", style_section))
            ped_data = [[
                Paragraph("Nº", style_cell_bold),
                Paragraph("Data/Hora", style_cell_bold),
                Paragraph("Cliente / Endereço", style_cell_bold),
                Paragraph("Produtos / Obs", style_cell_bold),
                Paragraph("Pagamento", style_cell_bold),
                Paragraph("Valor", style_cell_bold)
            ]]

            for p in self.dados_atuais["pedidos"]:
                obs_txt = f"<br/><font color='#718096'><i>Obs: {p.observacao}</i></font>" if p.observacao else ""
                ped_data.append([
                    Paragraph(f"<b>#{p.numero_pedido}</b>", style_cell),
                    Paragraph(f"{p.data}<br/>{p.hora}", style_cell),
                    Paragraph(f"<b>{p.cliente}</b><br/>{p.endereco}", style_cell),
                    Paragraph(f"{p.produto}{obs_txt}", style_cell),
                    Paragraph(p.pagamento, style_cell),
                    Paragraph(f"<b>R$ {p.valor:.2f}</b>".replace('.', ','), style_cell)
                ])

            t_ped = Table(ped_data, colWidths=[35, 65, 145, 170, 65, 55])
            t_ped.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            elements.append(t_ped)

            # Build do PDF
            doc.build(elements)

            # -------- ABRE O PDF PARA VISUALIZAÇÃO --------
            # O usuario decide, na propria tela do visualizador de PDF,
            # se quer imprimir, salvar em outro lugar ou so olhar.
            try:
                os.startfile(caminho_salvar)
            except Exception as e:
                messagebox.showerror(
                    "Erro ao abrir o PDF",
                    "O relatório foi gerado, mas não foi possível abri-lo "
                    f"automaticamente.\n\nVocê pode abrir manualmente em:\n{caminho_salvar}"
                )
            # -----------------------------------------------

        except Exception as e:
            messagebox.showerror("Erro ao Gerar PDF", f"Não foi possível gerar o arquivo PDF:\n{e}")