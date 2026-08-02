# Web/PWA Air Sense

Painel instalável, sem etapa de build e alinhado visualmente ao app mobile. A
interface prioriza o veredito, deixa evidente se a origem é live/demo/offline e
nunca apresenta o protótipo como instrumento certificado.

## Telas concluídas

| Tela | Conteúdo |
|---|---|
| Agora | veredito, ação prudente, cartões de CO₂/PM/VOC/T/RH e sparklines |
| Histórico | seleção de grandeza/período, série do backend e gráfico SVG |
| Alertas | eventos da sessão, contexto, horário e reconhecimento local |
| Dispositivo | conectividade, firmware, RSSI, heap, sensores e API/backend |

Em telas largas há navegação lateral; em celulares, barra inferior. Valores,
identificadores e mensagens remotas entram por propriedades textuais do DOM. Os
gráficos são SVG leve gerado somente de dados numéricos normalizados.

## Integração

O front usa same-origin por padrão:

```js
window.QAR_CONFIG = { apiBaseUrl: "", wsPath: "/ws" };
```

Para publicar em origem separada, ajuste `public/config.js` e configure no
backend `CORS_ORIGINS=https://origem.exata`. O WebSocket deriva `ws://` ou
`wss://` da URL base; não use origem `*` quando houver autenticação.

## PWA e estados

- `manifest.webmanifest`, `icon.svg` e `sw.js` permitem instalação;
- o service worker mantém somente o shell estático, não telemetria antiga;
- o banner distingue dados ao vivo, demonstração, reconexão e offline;
- falha de API pode ativar demo somente com sinalização visível;
- ações são recomendações experimentais, não alarmes de emergência.

## Verificação

```bash
cd ../backend
npm test
node --check ../web/public/app.js
node --check ../web/public/charts.js
node --check ../web/public/config.js
node --check ../web/public/sw.js
```

Testes end-to-end multiengine, auditoria formal WCAG/Lighthouse, push autenticado
e histórico agregado de longo prazo permanecem nos próximos marcos.
