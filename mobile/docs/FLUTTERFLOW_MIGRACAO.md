# Migração do protótipo FlutterFlow

## Resultado da inspeção

O ZIP `mobile_pages.zip` continha somente `pubspec.yaml`, três funções customizadas
e diretórios vazios; não havia código Dart gerado das páginas ou componentes. O
ZIP de YAML continha a definição visual completa do FlutterFlow e foi usado como
especificação, não como código executável.

As funções iniciais dependiam de classes geradas do FlutterFlow/Firebase que não
existiam no pacote. A reconstrução remove essa dependência e usa o backend real
do repositório.

## Mapeamento de páginas

| FlutterFlow | Implementação Flutter | Situação |
|---|---|---|
| `AuthPortal` | `ConnectionPage` | adaptado para conexão local e demo; não finge autenticação |
| `RealTimeDashboard` | `DashboardPage` | completo, REST + WebSocket |
| `HistoricalAnalytics` | `HistoryPage` | completo, janelas 6 h/24 h/7 dias |
| `AlertHistory` | `AlertsPage` | completo para alertas da sessão |
| `DeviceDetails` | `DeviceDetailsPage` | completo com sensores, RSSI e memória |
| `HardwareManagement` | `HardwareManagementPage` | completo em modo leitura/checklist |
| `UserSettings` | `SettingsPage` | completo com tema, alertas e conexão |

## Mapeamento de componentes

| Componentes do YAML | Substituição |
|---|---|
| `BottomNav`, `BottomNav2/3/4` | `NavigationBar` único e consistente |
| `AlertTile` | `_AlertTile` |
| `ConnectivityBanner` | `ConnectivityBanner` |
| `VerdictCard` | `VerdictCard` |
| `SensorCard` | `_SensorCard` e `MetricCard` |
| `SensorHealthTile`, `HealthRow` | `_HealthRow` |
| `InfoRow` | `InfoRow` |
| `CalibrationCard` | `_CalibrationCard` |
| `TimeframeChip` | `SegmentedButton<HistoryWindow>` |
| `AnalyticCard`, `AnalyticCard2/3` | `_AnalyticsCard` parametrizado |
| `SettingsGroup`, `SettingsGroup2/3` | `SurfaceCard` + `_SettingsTile` |
| `TextField`, `Button`, `SwitchComponent` | controles Material 3 temáticos |
| `NavItem`, `AdminActionCard`, `SsoProvider` | absorvidos pelo shell ou adiados por segurança |

Consolidar variantes duplicadas evita quatro barras inferiores e três cartões de
análise com manutenção separada.

## Identidade visual

O YAML usava azul-claro e fonte Inter. Para atender à continuidade pedida, o app
adota a linguagem da versão web: azul-marinho, verde-petróleo, fundos cinza
claros, superfícies brancas e cores semânticas de sucesso/atenção/perigo. O tema
escuro preserva contraste e hierarquia.

## Funcionalidades acrescentadas

- onboarding de URL com ajuda específica por plataforma;
- reconexão WebSocket e polling de contingência;
- estado explícito de demonstração;
- diagnóstico de REST, WebSocket e ingestão;
- dados de firmware/heap/RSSI;
- pinagem informada da placa e ressalvas elétricas;
- memória limitada para séries e alertas;
- testes automatizados e documentação de operação.
