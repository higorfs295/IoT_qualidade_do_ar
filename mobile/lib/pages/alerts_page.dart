import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../models/app_models.dart';
import '../state/app_controller.dart';
import '../widgets/common_widgets.dart';

class AlertsPage extends StatefulWidget {
  const AlertsPage({super.key, required this.controller});

  final AppController controller;

  @override
  State<AlertsPage> createState() => _AlertsPageState();
}

class _AlertsPageState extends State<AlertsPage> {
  bool _onlyActive = true;

  @override
  Widget build(BuildContext context) {
    final visible = widget.controller.alerts
        .where((alert) => !_onlyActive || !alert.acknowledged)
        .toList(growable: false);
    return ListView(
      key: const PageStorageKey('alerts-scroll'),
      padding: const EdgeInsets.fromLTRB(18, 22, 18, 120),
      children: [
        PageHeader(
          title: 'Alertas',
          subtitle: '${widget.controller.activeAlerts} pendentes nesta sessão',
          trailing: widget.controller.activeAlerts > 0
              ? TextButton(
                  onPressed: widget.controller.acknowledgeAll,
                  child: const Text('Reconhecer todos'),
                )
              : null,
        ),
        const SizedBox(height: 18),
        SegmentedButton<bool>(
          segments: const [
            ButtonSegment(value: true, label: Text('Pendentes')),
            ButtonSegment(value: false, label: Text('Todos')),
          ],
          selected: {_onlyActive},
          showSelectedIcon: false,
          onSelectionChanged: (value) {
            setState(() => _onlyActive = value.first);
          },
        ),
        const SizedBox(height: 16),
        SurfaceCard(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          color: AppPalette.tinted(context, AppPalette.neutral),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.info_outline_rounded, size: 19),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Alertas são derivados localmente das leituras recebidas e não representam um sistema certificado de segurança.',
                  style: Theme.of(
                    context,
                  ).textTheme.bodySmall?.copyWith(height: 1.4),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (visible.isEmpty)
          SurfaceCard(
            child: EmptyState(
              icon: _onlyActive
                  ? Icons.notifications_none_rounded
                  : Icons.history_toggle_off_rounded,
              title: _onlyActive
                  ? 'Tudo tranquilo'
                  : 'Nenhum alerta registrado',
              message: _onlyActive
                  ? 'Não há ocorrências aguardando reconhecimento.'
                  : 'Os eventos desta sessão aparecerão aqui.',
            ),
          )
        else
          for (final alert in visible) ...[
            _AlertTile(
              alert: alert,
              onAcknowledge: () => widget.controller.acknowledgeAlert(alert.id),
            ),
            const SizedBox(height: 11),
          ],
      ],
    );
  }
}

class _AlertTile extends StatelessWidget {
  const _AlertTile({required this.alert, required this.onAcknowledge});

  final AlertEvent alert;
  final VoidCallback onAcknowledge;

  @override
  Widget build(BuildContext context) {
    final (color, icon, label) = switch (alert.severity) {
      AlertSeverity.danger => (
        AppPalette.danger,
        Icons.warning_amber_rounded,
        'CRÍTICO',
      ),
      AlertSeverity.attention => (
        AppPalette.attention,
        Icons.info_outline_rounded,
        'ATENÇÃO',
      ),
      AlertSeverity.unavailable => (
        AppPalette.neutral,
        Icons.sensors_off_outlined,
        'INDISPONÍVEL',
      ),
    };
    return SurfaceCard(
      borderColor: alert.acknowledged
          ? AppPalette.border(context)
          : color.withValues(alpha: 0.38),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: color),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    StatusPill(label: label, color: color),
                    const Spacer(),
                    Text(
                      formatRelative(alert.timestamp),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppPalette.muted(context),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  alert.title,
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 4),
                Text(alert.description, style: const TextStyle(height: 1.35)),
                const SizedBox(height: 7),
                Text(
                  alert.deviceId,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppPalette.muted(context),
                  ),
                ),
                if (!alert.acknowledged) ...[
                  const SizedBox(height: 10),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton.icon(
                      onPressed: onAcknowledge,
                      icon: const Icon(Icons.done_rounded, size: 18),
                      label: const Text('Reconhecer'),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
