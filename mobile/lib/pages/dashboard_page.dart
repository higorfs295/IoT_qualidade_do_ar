import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../models/air_quality.dart';
import '../state/app_controller.dart';
import '../widgets/common_widgets.dart';
import 'device_details_page.dart';

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key, required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final telemetry = controller.currentTelemetry;
    final device = controller.selectedDevice;
    final verdict = verdictFor(telemetry);
    return RefreshIndicator(
      onRefresh: controller.refresh,
      child: CustomScrollView(
        key: const PageStorageKey('dashboard-scroll'),
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(18, 22, 18, 120),
            sliver: SliverList.list(
              children: [
                PageHeader(
                  title: 'Air Sense',
                  subtitle: device == null
                      ? 'Aguardando estação'
                      : '${device.siteId} • ${device.online ? 'online' : 'offline'}',
                  trailing: IconButton.filledTonal(
                    tooltip: 'Detalhes do dispositivo',
                    onPressed: device == null
                        ? null
                        : () => Navigator.of(context).push(
                            MaterialPageRoute<void>(
                              builder: (_) =>
                                  DeviceDetailsPage(controller: controller),
                            ),
                          ),
                    icon: const Icon(Icons.memory_rounded),
                  ),
                ),
                if (controller.devices.length > 1) ...[
                  const SizedBox(height: 17),
                  DropdownButtonFormField<String>(
                    initialValue: controller.selectedDeviceId,
                    decoration: const InputDecoration(
                      labelText: 'Estação',
                      prefixIcon: Icon(Icons.sensors_rounded),
                    ),
                    items: controller.devices
                        .map(
                          (item) => DropdownMenuItem(
                            value: item.deviceId,
                            child: Text(item.deviceId),
                          ),
                        )
                        .toList(growable: false),
                    onChanged: controller.selectDevice,
                  ),
                ],
                const SizedBox(height: 18),
                const PrototypeNotice(),
                const SizedBox(height: 15),
                VerdictCard(verdict: verdict, timestamp: telemetry?.sentAt),
                const SizedBox(height: 24),
                const SectionTitle(
                  title: 'Leituras atuais',
                  subtitle: 'Recebidas do ESP32 via MQTT e WebSocket',
                ),
                const SizedBox(height: 12),
                if (telemetry == null)
                  const SurfaceCard(
                    child: EmptyState(
                      icon: Icons.sensors_off_outlined,
                      title: 'Nenhuma telemetria ainda',
                      message:
                          'Assim que o dispositivo publicar, as leituras aparecerão aqui.',
                    ),
                  )
                else
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final columns = constraints.maxWidth >= 720 ? 3 : 2;
                      return GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: metricDefinitions.length,
                        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: columns,
                          crossAxisSpacing: 11,
                          mainAxisSpacing: 11,
                          mainAxisExtent: 205,
                        ),
                        itemBuilder: (context, index) {
                          final definition = metricDefinitions[index];
                          return MetricCard(
                            definition: definition,
                            value: telemetry.measurements.valueFor(
                              definition.field,
                            ),
                            points: _latestPoints(
                              controller.seriesFor(definition.field),
                              24,
                            ),
                          );
                        },
                      );
                    },
                  ),
                const SizedBox(height: 24),
                SectionTitle(
                  title: 'Fluxo do sistema',
                  subtitle: 'Diagnóstico da sessão atual',
                  trailing: IconButton(
                    tooltip: 'Atualizar',
                    onPressed: controller.refresh,
                    icon: const Icon(Icons.refresh_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                SurfaceCard(
                  child: Column(
                    children: [
                      InfoRow(
                        label: 'API REST',
                        value: controller.restConnected
                            ? 'Conectada'
                            : 'Indisponível',
                        icon: Icons.dns_outlined,
                        valueColor: controller.restConnected
                            ? AppPalette.good
                            : AppPalette.danger,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Tempo real',
                        value: controller.wsConnected
                            ? 'Ativo'
                            : 'Reconectando',
                        icon: Icons.swap_horiz_rounded,
                        valueColor: controller.wsConnected
                            ? AppPalette.good
                            : AppPalette.attention,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Mensagens válidas',
                        value: '${controller.backendMetrics.received}',
                        icon: Icons.check_circle_outline_rounded,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Mensagens inválidas',
                        value: '${controller.backendMetrics.invalid}',
                        icon: Icons.error_outline_rounded,
                        valueColor: controller.backendMetrics.invalid > 0
                            ? AppPalette.attention
                            : null,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  static List<T> _latestPoints<T>(List<T> values, int limit) {
    if (values.length <= limit) return values;
    return values.sublist(values.length - limit);
  }
}
