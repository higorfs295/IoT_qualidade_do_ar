# Web — painel instalável (PWA)

Dashboard **legível e conduzível por um usuário leigo**. A pessoa abre e entende
em 3 segundos se o ar está bom e o que fazer — sem jargão.

## Stack atual

- HTML/CSS/JavaScript sem etapa de build.
- `charts.js` com sparkline SVG sem dependências.
- REST + WebSocket do backend; modo mock para demonstração.
- Manifest, service worker e shell offline; pode ser instalado pelo navegador.
- Consome a API + WebSocket do [`../backend`](../backend).

## Princípios de legibilidade para leigos

- **Um veredito grande por cor:** um cartão central "Ar: BOM / ATENÇÃO / RUIM"
  em verde/amarelo/vermelho, derivado do `gas_status` e dos limiares.
- **Linguagem simples + ação prudente:** indicar verificação/ventilação sem
  transformar o protótipo em instrumento de segurança.
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

## Estrutura atual

```text
public/
├── index.html, style.css
├── app.js, charts.js, config.js
├── manifest.webmanifest, sw.js
└── icon.svg
```

Histórico longo, notificações push e paridade com um app nativo estão no
[`../../docs/ROADMAP_SOFTWARE.md`](../../docs/ROADMAP_SOFTWARE.md).
