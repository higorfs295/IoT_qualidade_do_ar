# Web — Painel gerencial MVP

Dashboard **legível e conduzível por um usuário leigo**. A pessoa abre e entende
em 3 segundos se o ar está bom e o que fazer — sem jargão.

## Stack atual

- HTML/CSS/JavaScript sem etapa de build.
- `charts.js` com sparkline SVG sem dependências.
- REST + WebSocket do backend; modo mock para demonstração.
- Consome a API + WebSocket do [`../backend`](../backend).

## Princípios de legibilidade para leigos

- **Um veredito grande por cor:** um cartão central "Ar: BOM / ATENÇÃO / RUIM"
  em verde/amarelo/vermelho, derivado do `gas_status` e dos limiares.
- **Linguagem simples + ação:** em vez de "PM2.5 = 82 µg/m³", mostrar
  "Partículas altas — **abra a janela**".
- **Cartões por grandeza** com ícone, valor grande, faixa de referência e uma
  **sparkline** de tendência (subindo/descendo).
- **Cores acessíveis** (não depender só de cor: usar ícone + texto).
- **Tempo real** via WebSocket, com "última atualização há X s".
- **Página de histórico** com gráficos de área por período (dia/semana).

## Evolução planejada

| Tela | Conteúdo |
|---|---|
| Agora | veredito grande + cartões por grandeza + sparklines |
| Histórico | gráficos de tendência por período e por grandeza |
| Alertas | eventos UNSAFE, com hora e o que fazer |
| Dispositivo | detalhes, status de conexão, firmware, RSSI |

## Estrutura sugerida

```text
web/
├── src/app/                # rotas (Next App Router): agora, historico, alertas
├── src/components/         # cartões, gráficos, veredito, layout
├── src/hooks/              # useTelemetria (TanStack Query + WebSocket)
├── tailwind + next.config
└── package.json
```

Next.js/TypeScript, histórico persistente, eventos e paridade mobile estão no
[`../../docs/ROADMAP_SOFTWARE.md`](../../docs/ROADMAP_SOFTWARE.md).
