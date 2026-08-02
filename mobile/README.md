# Mobile — PWA funcional e Flutter opcional

O caminho mobile utilizável agora é a PWA em [`../dashboard/web`](../dashboard/web):
abra o dashboard pelo navegador do celular e escolha **Instalar app**. Ela usa a
mesma API/WebSocket, possui shell offline e não exige uma segunda base de código.

## Aplicativo Flutter futuro

Aplicativo mobile em **Flutter**, consumindo a **mesma API + WebSocket** do
[`../dashboard/backend`](../dashboard/backend) — paridade total com o web.

> Status: a PWA está implementada; Flutter permanece opcional para notificações
> nativas, distribuição em lojas e integrações específicas de Android/iOS.

Plano executável e gates: [`../docs/ROADMAP_SOFTWARE.md`](../docs/ROADMAP_SOFTWARE.md).

## Por que Flutter

- Um só código para Android e iOS.
- Ótimo para telemetria em tempo real (streams) e gráficos.
- Preferência do projeto.

## Telas

| Tela | Conteúdo |
|---|---|
| Agora | veredito grande por cor (BOM/ATENÇÃO/RUIM) + cartões por grandeza |
| Histórico | gráficos por período (`fl_chart`) |
| Alertas | notificações push quando o ar fica `UNSAFE` |
| Dispositivos | status de conexão, firmware, RSSI |

## Stack sugerida

- **Estado:** Riverpod (ou Bloc).
- **Rede:** `dio` (REST) + `web_socket_channel` (tempo real).
- **Gráficos:** `fl_chart`.
- **Notificações:** `flutter_local_notifications` + push (FCM) para alertas.

## Estrutura sugerida

```text
mobile/
├── lib/
│   ├── main.dart
│   ├── api/            # cliente REST + WebSocket (mesma API do backend)
│   ├── modelos/        # Telemetria (espelha o contrato v1.1)
│   ├── telas/          # agora, historico, alertas, dispositivos
│   └── widgets/        # veredito, cartão de grandeza, gráfico
└── pubspec.yaml
```

## Coerência

O modelo `Telemetria` no app espelha o **contrato v1.1** (mesmos campos do
firmware e do Python). O **veredito por cor** usa os mesmos limiares do backend
e do firmware (`config.h`), garantindo que web, mobile e dispositivo "concordem"
sobre o que é ar bom ou ruim.
