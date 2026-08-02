import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import 'telemetry.dart';

enum AirLevel { good, attention, danger, unavailable }

class AirVerdict {
  const AirVerdict({
    required this.level,
    required this.title,
    required this.description,
    required this.icon,
  });

  final AirLevel level;
  final String title;
  final String description;
  final IconData icon;

  Color get color => switch (level) {
    AirLevel.good => AppPalette.good,
    AirLevel.attention => AppPalette.attention,
    AirLevel.danger => AppPalette.danger,
    AirLevel.unavailable => AppPalette.neutral,
  };
}

class MetricDefinition {
  const MetricDefinition({
    required this.field,
    required this.label,
    required this.shortLabel,
    required this.unit,
    required this.icon,
    required this.reference,
    this.attentionAt,
    this.dangerAt,
    this.decimals = 0,
  });

  final String field;
  final String label;
  final String shortLabel;
  final String unit;
  final IconData icon;
  final String reference;
  final double? attentionAt;
  final double? dangerAt;
  final int decimals;

  AirLevel levelFor(double? value) {
    if (value == null) return AirLevel.unavailable;
    if (dangerAt != null && value >= dangerAt!) return AirLevel.danger;
    if (attentionAt != null && value >= attentionAt!) {
      return AirLevel.attention;
    }
    return AirLevel.good;
  }

  String format(double? value) {
    if (value == null) return '--';
    return value.toStringAsFixed(decimals);
  }
}

const metricDefinitions = <MetricDefinition>[
  MetricDefinition(
    field: 'co2_ppm',
    label: 'Gás carbônico',
    shortLabel: 'CO₂',
    unit: 'ppm',
    icon: Icons.co2_rounded,
    reference: 'faixa operacional: bom < 800',
    attentionAt: 800,
    dangerAt: 1000,
  ),
  MetricDefinition(
    field: 'pm25_ugm3',
    label: 'Poeira fina',
    shortLabel: 'PM2.5',
    unit: 'µg/m³',
    icon: Icons.blur_on_rounded,
    reference: 'faixa operacional: bom < 25',
    attentionAt: 25,
    dangerAt: 35,
    decimals: 1,
  ),
  MetricDefinition(
    field: 'pm10_ugm3',
    label: 'Partículas',
    shortLabel: 'PM10',
    unit: 'µg/m³',
    icon: Icons.grain_rounded,
    reference: 'faixa operacional: bom < 50',
    attentionAt: 50,
    dangerAt: 80,
    decimals: 1,
  ),
  MetricDefinition(
    field: 'voc_index',
    label: 'Compostos voláteis',
    shortLabel: 'VOC',
    unit: 'índice',
    icon: Icons.science_rounded,
    reference: 'índice relativo; ~100 é típico',
    attentionAt: 150,
    dangerAt: 250,
  ),
  MetricDefinition(
    field: 'temperature_c',
    label: 'Temperatura',
    shortLabel: 'Temp.',
    unit: '°C',
    icon: Icons.thermostat_rounded,
    reference: 'conforto indicativo: 20–26 °C',
    decimals: 1,
  ),
  MetricDefinition(
    field: 'humidity_pct',
    label: 'Umidade',
    shortLabel: 'Umidade',
    unit: '%',
    icon: Icons.water_drop_rounded,
    reference: 'conforto indicativo: 40–60%',
    decimals: 1,
  ),
  MetricDefinition(
    field: 'pm1_ugm3',
    label: 'Partículas finas',
    shortLabel: 'PM1',
    unit: 'µg/m³',
    icon: Icons.auto_awesome_rounded,
    reference: 'faixa operacional: bom < 20',
    attentionAt: 20,
    dangerAt: 30,
    decimals: 1,
  ),
  MetricDefinition(
    field: 'gas_raw_v',
    label: 'Canal de gás bruto',
    shortLabel: 'Gás bruto',
    unit: 'V',
    icon: Icons.electric_bolt_rounded,
    reference: 'diagnóstico; não equivale a ppm',
    decimals: 2,
  ),
];

AirVerdict verdictFor(Telemetry? telemetry) {
  if (telemetry == null ||
      telemetry.quality.sensorStatus == 'ERROR' ||
      telemetry.quality.gasStatus == 'UNKNOWN') {
    return const AirVerdict(
      level: AirLevel.unavailable,
      title: 'Sem dados confiáveis',
      description: 'Verifique a conexão e a saúde dos sensores.',
      icon: Icons.help_outline_rounded,
    );
  }
  if (telemetry.quality.gasStatus == 'UNSAFE') {
    return const AirVerdict(
      level: AirLevel.danger,
      title: 'Leitura elevada',
      description: 'Confirme com instrumento adequado e siga o plano do local.',
      icon: Icons.warning_amber_rounded,
    );
  }

  var worst = AirLevel.good;
  for (final metric in metricDefinitions) {
    final level = metric.levelFor(
      telemetry.measurements.valueFor(metric.field),
    );
    if (level == AirLevel.danger) worst = AirLevel.danger;
    if (level == AirLevel.attention && worst == AirLevel.good) {
      worst = AirLevel.attention;
    }
  }
  if (worst == AirLevel.danger) {
    return const AirVerdict(
      level: AirLevel.danger,
      title: 'Leitura elevada',
      description: 'Investigue ventilação e possíveis fontes de poluição.',
      icon: Icons.warning_amber_rounded,
    );
  }
  if (worst == AirLevel.attention ||
      telemetry.quality.sensorStatus == 'DEGRADED') {
    return const AirVerdict(
      level: AirLevel.attention,
      title: 'Atenção',
      description: 'Observe a tendência e verifique a ventilação.',
      icon: Icons.info_outline_rounded,
    );
  }
  return const AirVerdict(
    level: AirLevel.good,
    title: 'Ar bom',
    description: 'Leituras dentro das faixas operacionais do protótipo.',
    icon: Icons.check_circle_outline_rounded,
  );
}
