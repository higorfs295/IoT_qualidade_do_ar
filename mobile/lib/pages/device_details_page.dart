import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../state/app_controller.dart';
import '../widgets/common_widgets.dart';

class DeviceDetailsPage extends StatelessWidget {
  const DeviceDetailsPage({super.key, required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final device = controller.selectedDevice;
    final telemetry = controller.currentTelemetry;
    final metadata = telemetry?.metadata;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Detalhes do dispositivo'),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: controller.refresh,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: device == null
          ? const EmptyState(
              icon: Icons.sensors_off_outlined,
              title: 'Nenhum dispositivo',
              message: 'Conecte uma estação para consultar os detalhes.',
            )
          : ListView(
              padding: const EdgeInsets.fromLTRB(18, 10, 18, 50),
              children: [
                SurfaceCard(
                  color: AppPalette.tinted(
                    context,
                    device.online ? AppPalette.good : AppPalette.neutral,
                  ),
                  borderColor:
                      (device.online ? AppPalette.good : AppPalette.neutral)
                          .withValues(alpha: 0.3),
                  child: Row(
                    children: [
                      Container(
                        width: 55,
                        height: 55,
                        decoration: BoxDecoration(
                          color: AppPalette.teal.withValues(alpha: 0.13),
                          borderRadius: BorderRadius.circular(17),
                        ),
                        child: const Icon(
                          Icons.developer_board_rounded,
                          color: AppPalette.teal,
                          size: 29,
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              device.deviceId,
                              style: Theme.of(context).textTheme.titleLarge
                                  ?.copyWith(fontWeight: FontWeight.w900),
                            ),
                            const SizedBox(height: 3),
                            Text(
                              device.siteId,
                              style: TextStyle(
                                color: AppPalette.muted(context),
                              ),
                            ),
                          ],
                        ),
                      ),
                      StatusPill(
                        label: device.online ? 'ONLINE' : 'OFFLINE',
                        color: device.online
                            ? AppPalette.good
                            : AppPalette.neutral,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                const SectionTitle(title: 'Saúde dos sensores'),
                const SizedBox(height: 10),
                SurfaceCard(
                  child: Column(
                    children: [
                      _HealthRow(
                        icon: Icons.air_rounded,
                        label: 'Conjunto ambiental',
                        value: telemetry?.quality.sensorStatus ?? 'SEM DADOS',
                        healthy: telemetry?.quality.sensorStatus == 'OK',
                      ),
                      const Divider(height: 1),
                      _HealthRow(
                        icon: Icons.local_fire_department_outlined,
                        label: 'Canal de gases',
                        value: telemetry?.quality.gasStatus ?? 'SEM DADOS',
                        healthy: telemetry?.quality.gasStatus == 'SAFE',
                      ),
                      const Divider(height: 1),
                      _HealthRow(
                        icon: Icons.wifi_rounded,
                        label: 'Sinal Wi-Fi',
                        value: metadata?.rssiDbm == null
                            ? '--'
                            : '${metadata!.rssiDbm} dBm',
                        healthy: (metadata?.rssiDbm ?? -100) >= -75,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                const SectionTitle(title: 'Firmware e placa'),
                const SizedBox(height: 10),
                SurfaceCard(
                  child: Column(
                    children: [
                      InfoRow(
                        label: 'Modelo',
                        value: metadata?.boardModel ?? 'ESP-WROOM-32',
                        icon: Icons.memory_rounded,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Revisão de hardware',
                        value: metadata?.hardwareRevision ?? '--',
                        icon: Icons.developer_board_outlined,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Firmware',
                        value: metadata?.firmwareVersion ?? '--',
                        icon: Icons.code_rounded,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Modo dos sensores',
                        value: metadata?.sensorMode ?? '--',
                        icon: Icons.tune_rounded,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Boot ID',
                        value: metadata?.bootId ?? '--',
                        icon: Icons.fingerprint_rounded,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Sequência',
                        value: telemetry == null
                            ? '--'
                            : '${telemetry.sequence}',
                        icon: Icons.numbers_rounded,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                const SectionTitle(title: 'Memória e execução'),
                const SizedBox(height: 10),
                SurfaceCard(
                  child: Column(
                    children: [
                      InfoRow(
                        label: 'Heap livre',
                        value: _formatBytes(metadata?.freeHeapBytes),
                        icon: Icons.memory_outlined,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Menor heap livre',
                        value: _formatBytes(metadata?.minFreeHeapBytes),
                        icon: Icons.trending_down_rounded,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Maior bloco alocável',
                        value: _formatBytes(metadata?.maxAllocHeapBytes),
                        icon: Icons.data_object_rounded,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Tempo ligado',
                        value: formatUptime(metadata?.uptimeSeconds),
                        icon: Icons.timer_outlined,
                      ),
                      const Divider(height: 1),
                      InfoRow(
                        label: 'Última amostra',
                        value: telemetry == null
                            ? '--'
                            : formatDateTime(telemetry.sentAt),
                        icon: Icons.schedule_rounded,
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }

  static String _formatBytes(int? value) {
    if (value == null) return '--';
    return '${(value / 1024).toStringAsFixed(1)} KiB';
  }
}

class _HealthRow extends StatelessWidget {
  const _HealthRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.healthy,
  });

  final IconData icon;
  final String label;
  final String value;
  final bool healthy;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 12),
    child: Row(
      children: [
        Icon(icon, color: healthy ? AppPalette.good : AppPalette.attention),
        const SizedBox(width: 11),
        Expanded(
          child: Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
        ),
        StatusPill(
          label: value,
          color: healthy ? AppPalette.good : AppPalette.attention,
        ),
      ],
    ),
  );
}
