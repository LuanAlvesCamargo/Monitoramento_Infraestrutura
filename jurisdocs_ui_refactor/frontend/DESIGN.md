---
version: alpha
name: JurisDocs
description: Aplicação local para catalogar e consultar documentos jurídicos fictícios, com a clareza operacional de um sistema de tramitação documental.
colors:
  ground: "#eef3f7"
  ink: "#172b3a"
  muted: "#4f6170"
  signal: "#1d5d86"
typography:
  display:
    fontFamily: "Georgia, serif"
    fontSize: "2rem"
    fontWeight: "700"
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Arial, sans-serif"
    fontSize: "0.9375rem"
    lineHeight: "1.5"
rounded:
  sm: "4px"
  md: "8px"
spacing:
  sm: "0.5rem"
  md: "1rem"
  lg: "1.75rem"
components:
  button-primary:
    backgroundColor: "{colors.signal}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "0.7rem 1rem"
---

## Overview

JurisDocs é um catálogo acadêmico de documentos jurídicos fictícios, destinado a demonstrar CRUD em MongoDB e cache-aside em Redis. A aparência toma como ponto de partida os artefatos que usuários de sistemas processuais realmente manipulam: uma barra de consulta, filtros explícitos, registros numerados, uma tabela de resultados e estados documentais legíveis.

## Colors

- **Ground (#eef3f7):** cinza-azulado de área de trabalho, para manter foco no registro.
- **Ink (#172b3a):** azul profundo de texto e navegação, com contraste alto no fundo.
- **Muted (#4f6170):** texto secundário legível, usado para contexto e metadados.
- **Signal (#1d5d86):** azul de ação; serve somente para ações e foco ativo.
- **Brass (#9c6b26):** cor semântica de revisão, não usada como cor de marca.

## Typography

Georgia é reservada ao nome do sistema e aos títulos de área, remetendo a documentos formais. Arial é usada nos dados e controles pela legibilidade compacta. Não há palavras isoladas coloridas, microtítulos decorativos ou fonte monoespaçada usada como ornamento.

## Layout

O aplicativo se comporta como uma estação de trabalho: cabeçalho de serviço, navegação lateral persistente e uma superfície de consulta. A tabela, e não cartões promocionais, é a peça dominante. O resumo de contagens representa valores reais da consulta atual.

## Elevation & Depth

Somente a janela de cadastro se sobrepõe à página. Painéis cotidianos usam divisórias e fundo, não sombras difusas.

## Shapes

Controles usam raio discreto de 4px; áreas principais usam 8px. Etiquetas de status são compactas e representam estados reais do documento.

## Components

A navegação lateral, barra de filtros, resumo de registros, tabela e formulário lateral pertencem ao mesmo sistema. Novas páginas devem reutilizar estes tokens e o mesmo cabeçalho.

## Do's and Don'ts

- Reutilizar cores, tipografia e espaçamento deste arquivo.
- Priorizar filtros, tabela e estado real dos dados sobre elementos decorativos.
- Não usar gradiente roxo/azul, fundo creme com terracota, tema escuro com neon, cards idênticos como composição, hero centralizado ou rótulos em caixa alta decorativos.
