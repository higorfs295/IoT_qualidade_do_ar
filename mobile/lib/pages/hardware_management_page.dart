import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../state/app_controller.dart';
import '../widgets/common_widgets.dart';

class HardwareManagementPage extends StatelessWidget {
  const HardwareManagementPage({super.key, required this.controller});

  final AppController controller;

  static const pinPairs = <(String, String)>[
    ('3V3', 'VIN'),
    ('GND', 'GND'),
    ('D15', 'D13'),
    ('D2', 'D12'),
    ('D4', 'D14'),
    ('D16', 'D27'),
    ('D17', 'D26'),
    ('D5', 'D25'),
    ('D18', 'D33'),
    ('D19', 'D32'),
    ('D21', 'D35'),
    ('RX0', 'D34'),
    ('TX0', 'VIN'),
    ('D22', 'VP'),
    ('D23', 'EN'),
  ];

  @override
  Widget build(BuildContext context) {
    final telemetry = controller.currentTelemetry;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Hardware e calibração'),
        actions: [
          IconButton(
            tooltip: 'Atualizar diagnóstico',
            onPressed: controller.refresh,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(18, 10, 18, 50),
        children: [
          const PrototypeNotice(),
          const SizedBox(height: 20),
          const SectionTitle(
            title: 'Placa controladora',
            subtitle: 'ESP32 Wi-Fi ESP-WROOM-32 • DevKit 30 pinos USB-C',
          ),
          const SizedBox(height: 10),
          SurfaceCard(
            child: Column(
              children: [
                Row(
                  children: [
                    Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: AppPalette.teal.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Icon(
                        Icons.developer_board_rounded,
                        color: AppPalette.teal,
                        size: 28,
                      ),
                    ),
                    const SizedBox(width: 13),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'ESP-WROOM-32',
                            style: TextStyle(fontWeight: FontWeight.w900),
                          ),
                          SizedBox(height: 3),
                          Text('Wi-Fi 2,4 GHz • alimentação via USB-C'),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 15),
                InfoRow(
                  label: 'Firmware observado',
                  value: telemetry?.metadata.firmwareVersion ?? '--',
                ),
                const Divider(height: 1),
                InfoRow(
                  label: 'Revisão',
                  value: telemetry?.metadata.hardwareRevision ?? '--',
                ),
              ],
            ),
          ),
          const SizedBox(height: 22),
          const SectionTitle(
            title: 'Mapa físico informado',
            subtitle:
                'Vista superior: BOOT à esquerda, USB-C ao centro e EN à direita',
          ),
          const SizedBox(height: 10),
          SurfaceCard(
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 10,
                  ),
                  decoration: BoxDecoration(
                    color: AppPalette.navy,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'BOOT',
                        style: TextStyle(color: Colors.white, fontSize: 11),
                      ),
                      Text(
                        'USB-C',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      Text(
                        'EN',
                        style: TextStyle(color: Colors.white, fontSize: 11),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 9),
                for (var index = 0; index < pinPairs.length; index++) ...[
                  _PinRow(left: pinPairs[index].$1, right: pinPairs[index].$2),
                  if (index != pinPairs.length - 1) const Divider(height: 1),
                ],
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppPalette.attention.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        Icons.warning_amber_rounded,
                        color: AppPalette.attention,
                        size: 20,
                      ),
                      SizedBox(width: 9),
                      Expanded(
                        child: Text(
                          'Confirme o modelo exato com multímetro e desenho dimensional antes da PCB. D34, D35 e VP são entradas; a repetição de VIN reproduz a serigrafia informada.',
                          style: TextStyle(height: 1.4, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 22),
          const SectionTitle(
            title: 'Sensores e interfaces',
            subtitle: 'Estado derivado da telemetria mais recente',
          ),
          const SizedBox(height: 10),
          _SensorCard(
            title: 'Partículas e ambiente',
            subtitle: 'PM1, PM2.5, PM10, temperatura e umidade',
            icon: Icons.blur_on_rounded,
            status: telemetry?.quality.sensorStatus ?? 'SEM DADOS',
            healthy: telemetry?.quality.sensorStatus == 'OK',
          ),
          const SizedBox(height: 10),
          _SensorCard(
            title: 'Qualidade gasosa',
            subtitle: 'CO₂, VOC e canal analógico bruto',
            icon: Icons.science_outlined,
            status: telemetry?.quality.gasStatus ?? 'SEM DADOS',
            healthy: telemetry?.quality.gasStatus == 'SAFE',
          ),
          const SizedBox(height: 22),
          const SectionTitle(
            title: 'Calibração assistida',
            subtitle:
                'Procedimentos seguros que exigem presença no equipamento',
          ),
          const SizedBox(height: 10),
          const _CalibrationCard(
            title: 'Baseline em ar limpo',
            description:
                'Estabilize a estação no ambiente de referência, registre temperatura/umidade e compare com instrumento rastreável.',
            steps: [
              'Aquecimento concluído',
              'Ambiente estável',
              'Referência registrada',
            ],
          ),
          const SizedBox(height: 10),
          const _CalibrationCard(
            title: 'Validação de partículas',
            description:
                'Faça co-localização, registre uma série longa e calcule correção somente após avaliar erro e repetibilidade.',
            steps: ['Fluxo de ar livre', 'Co-localização', 'Relatório de erro'],
          ),
          const SizedBox(height: 15),
          FilledButton.icon(
            onPressed: null,
            icon: const Icon(Icons.lock_outline_rounded),
            label: const Text('Comandos remotos não habilitados'),
          ),
          const SizedBox(height: 8),
          Text(
            'O backend atual é somente leitura. Calibração remota deve exigir autenticação, autorização, trilha de auditoria e confirmação física.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppPalette.muted(context),
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _PinRow extends StatelessWidget {
  const _PinRow({required this.left, required this.right});

  final String left;
  final String right;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 7),
    child: Row(
      children: [
        _Pin(label: left, align: Alignment.centerLeft),
        Expanded(
          child: Container(
            height: 1,
            margin: const EdgeInsets.symmetric(horizontal: 8),
            color: AppPalette.border(context),
          ),
        ),
        _Pin(label: right, align: Alignment.centerRight),
      ],
    ),
  );
}

class _Pin extends StatelessWidget {
  const _Pin({required this.label, required this.align});

  final String label;
  final Alignment align;

  @override
  Widget build(BuildContext context) => Container(
    width: 52,
    alignment: align,
    child: Text(
      label,
      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12),
    ),
  );
}

class _SensorCard extends StatelessWidget {
  const _SensorCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.status,
    required this.healthy,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final String status;
  final bool healthy;

  @override
  Widget build(BuildContext context) => SurfaceCard(
    child: Row(
      children: [
        Icon(icon, color: healthy ? AppPalette.good : AppPalette.attention),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
              const SizedBox(height: 3),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppPalette.muted(context),
                ),
              ),
            ],
          ),
        ),
        StatusPill(
          label: status,
          color: healthy ? AppPalette.good : AppPalette.attention,
        ),
      ],
    ),
  );
}

class _CalibrationCard extends StatelessWidget {
  const _CalibrationCard({
    required this.title,
    required this.description,
    required this.steps,
  });

  final String title;
  final String description;
  final List<String> steps;

  @override
  Widget build(BuildContext context) => SurfaceCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 7),
        Text(description, style: const TextStyle(height: 1.4)),
        const SizedBox(height: 12),
        for (final step in steps)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Row(
              children: [
                const Icon(
                  Icons.radio_button_unchecked_rounded,
                  size: 17,
                  color: AppPalette.teal,
                ),
                const SizedBox(width: 8),
                Text(step),
              ],
            ),
          ),
      ],
    ),
  );
}
