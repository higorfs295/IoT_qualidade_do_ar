import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../models/air_quality.dart';
import '../models/app_models.dart';

class SurfaceCard extends StatelessWidget {
  const SurfaceCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.color,
    this.borderColor,
    this.onTap,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color? color;
  final Color? borderColor;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final decoration = BoxDecoration(
      color: color ?? AppPalette.surface(context),
      borderRadius: BorderRadius.circular(20),
      border: Border.all(color: borderColor ?? AppPalette.border(context)),
      boxShadow: Theme.of(context).brightness == Brightness.light
          ? const [
              BoxShadow(
                color: Color(0x0A0F172A),
                blurRadius: 20,
                offset: Offset(0, 8),
              ),
            ]
          : null,
    );
    final content = Padding(padding: padding, child: child);
    if (onTap == null) {
      return Material(
        color: Colors.transparent,
        child: Ink(decoration: decoration, child: content),
      );
    }
    return Material(
      color: Colors.transparent,
      child: Ink(
        decoration: decoration,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(20),
          child: content,
        ),
      ),
    );
  }
}

class PageHeader extends StatelessWidget {
  const PageHeader({
    super.key,
    required this.title,
    required this.subtitle,
    this.trailing,
  });

  final String title;
  final String subtitle;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) => Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w900,
                letterSpacing: -0.6,
              ),
            ),
            const SizedBox(height: 4),
            Text(subtitle, style: TextStyle(color: AppPalette.muted(context))),
          ],
        ),
      ),
      if (trailing != null) ...[const SizedBox(width: 12), trailing!],
    ],
  );
}

class SectionTitle extends StatelessWidget {
  const SectionTitle({
    super.key,
    required this.title,
    this.subtitle,
    this.trailing,
  });

  final String title;
  final String? subtitle;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) => Row(
    crossAxisAlignment: CrossAxisAlignment.end,
    children: [
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            if (subtitle != null) ...[
              const SizedBox(height: 3),
              Text(
                subtitle!,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppPalette.muted(context),
                ),
              ),
            ],
          ],
        ),
      ),
      trailing ?? const SizedBox.shrink(),
    ],
  );
}

class PrototypeNotice extends StatelessWidget {
  const PrototypeNotice({super.key});

  @override
  Widget build(BuildContext context) => SurfaceCard(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    color: AppPalette.tinted(context, AppPalette.blue),
    borderColor: AppPalette.blue.withValues(alpha: 0.3),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Icon(Icons.science_outlined, size: 19, color: AppPalette.blue),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            'Protótipo acadêmico: as faixas são operacionais e não substituem instrumentos certificados.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              height: 1.35,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    ),
  );
}

class ConnectivityBanner extends StatelessWidget {
  const ConnectivityBanner({
    super.key,
    required this.restConnected,
    required this.wsConnected,
    required this.demoMode,
    this.onRetry,
  });

  final bool restConnected;
  final bool wsConnected;
  final bool demoMode;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final (color, icon, text) = demoMode
        ? (AppPalette.blue, Icons.science_outlined, 'Modo demonstração')
        : !restConnected
        ? (AppPalette.danger, Icons.cloud_off_outlined, 'API desconectada')
        : !wsConnected
        ? (
            AppPalette.attention,
            Icons.sync_problem_outlined,
            'Tempo real reconectando',
          )
        : (
            AppPalette.good,
            Icons.cloud_done_outlined,
            'Conectado em tempo real',
          );
    return ColoredBox(
      color: color.withValues(alpha: 0.12),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 9),
          child: Row(
            children: [
              Icon(icon, size: 17, color: color),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  text,
                  style: TextStyle(
                    color: color,
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              if (!demoMode && (!restConnected || !wsConnected))
                TextButton(
                  onPressed: onRetry,
                  style: TextButton.styleFrom(
                    foregroundColor: color,
                    visualDensity: VisualDensity.compact,
                  ),
                  child: const Text('Tentar agora'),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class StatusPill extends StatelessWidget {
  const StatusPill({
    super.key,
    required this.label,
    required this.color,
    this.icon,
  });

  final String label;
  final Color color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
    decoration: BoxDecoration(
      color: color.withValues(alpha: 0.12),
      borderRadius: BorderRadius.circular(999),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (icon != null) ...[
          Icon(icon, color: color, size: 14),
          const SizedBox(width: 5),
        ],
        Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: 11,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    ),
  );
}

class VerdictCard extends StatelessWidget {
  const VerdictCard({
    super.key,
    required this.verdict,
    required this.timestamp,
  });

  final AirVerdict verdict;
  final DateTime? timestamp;

  @override
  Widget build(BuildContext context) => SurfaceCard(
    color: AppPalette.tinted(context, verdict.color),
    borderColor: verdict.color.withValues(alpha: 0.38),
    child: Row(
      children: [
        Container(
          width: 54,
          height: 54,
          decoration: BoxDecoration(
            color: verdict.color.withValues(alpha: 0.16),
            shape: BoxShape.circle,
          ),
          child: Icon(verdict.icon, color: verdict.color, size: 29),
        ),
        const SizedBox(width: 15),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                verdict.title,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w900,
                  color: verdict.color,
                ),
              ),
              const SizedBox(height: 3),
              Text(verdict.description),
              if (timestamp != null) ...[
                const SizedBox(height: 7),
                Text(
                  'Atualizado ${formatRelative(timestamp!)}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppPalette.muted(context),
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

class MetricCard extends StatelessWidget {
  const MetricCard({
    super.key,
    required this.definition,
    required this.value,
    this.points = const [],
  });

  final MetricDefinition definition;
  final double? value;
  final List<SeriesPoint> points;

  @override
  Widget build(BuildContext context) {
    final level = definition.levelFor(value);
    final color = colorForLevel(level);
    return SurfaceCard(
      padding: const EdgeInsets.all(15),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(definition.icon, size: 20, color: color),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  definition.shortLabel,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(color: color, shape: BoxShape.circle),
              ),
            ],
          ),
          const SizedBox(height: 13),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                  text: definition.format(value),
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w900,
                    letterSpacing: -0.7,
                  ),
                ),
                TextSpan(
                  text: ' ${definition.unit}',
                  style: TextStyle(
                    color: AppPalette.muted(context),
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 9),
          SizedBox(
            height: 30,
            width: double.infinity,
            child: MiniLineChart(points: points, color: color, showFill: true),
          ),
          const SizedBox(height: 7),
          Text(
            definition.reference,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppPalette.muted(context),
              height: 1.2,
              fontSize: 10.5,
            ),
          ),
        ],
      ),
    );
  }
}

class InfoRow extends StatelessWidget {
  const InfoRow({
    super.key,
    required this.label,
    required this.value,
    this.icon,
    this.valueColor,
  });

  final String label;
  final String value;
  final IconData? icon;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 10),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (icon != null) ...[
          Icon(icon, size: 19, color: AppPalette.muted(context)),
          const SizedBox(width: 10),
        ],
        Expanded(
          child: Text(
            label,
            style: TextStyle(color: AppPalette.muted(context)),
          ),
        ),
        const SizedBox(width: 14),
        Flexible(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: TextStyle(fontWeight: FontWeight.w700, color: valueColor),
          ),
        ),
      ],
    ),
  );
}

class EmptyState extends StatelessWidget {
  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.action,
  });

  final IconData icon;
  final String title;
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 54, color: AppPalette.muted(context)),
          const SizedBox(height: 16),
          Text(
            title,
            textAlign: TextAlign.center,
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: TextStyle(color: AppPalette.muted(context), height: 1.4),
          ),
          if (action != null) ...[const SizedBox(height: 20), action!],
        ],
      ),
    ),
  );
}

class MiniLineChart extends StatelessWidget {
  const MiniLineChart({
    super.key,
    required this.points,
    required this.color,
    this.showFill = false,
  });

  final List<SeriesPoint> points;
  final Color color;
  final bool showFill;

  @override
  Widget build(BuildContext context) => CustomPaint(
    painter: _LineChartPainter(
      values: points.map((point) => point.value).whereType<double>().toList(),
      color: color,
      gridColor: AppPalette.border(context),
      showFill: showFill,
    ),
  );
}

class _LineChartPainter extends CustomPainter {
  const _LineChartPainter({
    required this.values,
    required this.color,
    required this.gridColor,
    required this.showFill,
  });

  final List<double> values;
  final Color color;
  final Color gridColor;
  final bool showFill;

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;
    final gridPaint = Paint()
      ..color = gridColor.withValues(alpha: 0.7)
      ..strokeWidth = 1;
    for (var row = 0; row <= 3; row++) {
      final y = size.height * row / 3;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }
    if (values.length < 2) {
      final dash = Paint()
        ..color = gridColor
        ..strokeWidth = 2;
      canvas.drawLine(
        Offset(0, size.height / 2),
        Offset(size.width, size.height / 2),
        dash,
      );
      return;
    }
    final minimum = values.reduce(math.min);
    final maximum = values.reduce(math.max);
    final span = math.max(maximum - minimum, maximum.abs() * 0.08 + 0.01);
    final path = Path();
    for (var index = 0; index < values.length; index++) {
      final x = size.width * index / (values.length - 1);
      final normalized = (values[index] - minimum) / span;
      final y =
          size.height - (normalized * size.height * 0.82 + size.height * 0.09);
      if (index == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    if (showFill) {
      final fill = Path.from(path)
        ..lineTo(size.width, size.height)
        ..lineTo(0, size.height)
        ..close();
      canvas.drawPath(
        fill,
        Paint()
          ..shader = LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              color.withValues(alpha: 0.22),
              color.withValues(alpha: 0.01),
            ],
          ).createShader(Offset.zero & size),
      );
    }
    canvas.drawPath(
      path,
      Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.2
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );
  }

  @override
  bool shouldRepaint(covariant _LineChartPainter oldDelegate) =>
      oldDelegate.values != values ||
      oldDelegate.color != color ||
      oldDelegate.gridColor != gridColor ||
      oldDelegate.showFill != showFill;
}

Color colorForLevel(AirLevel level) => switch (level) {
  AirLevel.good => AppPalette.good,
  AirLevel.attention => AppPalette.attention,
  AirLevel.danger => AppPalette.danger,
  AirLevel.unavailable => AppPalette.neutral,
};

String formatRelative(DateTime timestamp) {
  final difference = DateTime.now().difference(timestamp);
  if (difference.inSeconds < 10) return 'agora';
  if (difference.inMinutes < 1) return 'há ${difference.inSeconds}s';
  if (difference.inHours < 1) return 'há ${difference.inMinutes}min';
  if (difference.inDays < 1) return 'há ${difference.inHours}h';
  return 'há ${difference.inDays}d';
}

String formatDateTime(DateTime timestamp) {
  String two(int value) => value.toString().padLeft(2, '0');
  return '${two(timestamp.day)}/${two(timestamp.month)}/${timestamp.year} '
      '${two(timestamp.hour)}:${two(timestamp.minute)}';
}

String formatUptime(int? seconds) {
  if (seconds == null) return '--';
  final days = seconds ~/ 86400;
  final hours = (seconds % 86400) ~/ 3600;
  final minutes = (seconds % 3600) ~/ 60;
  if (days > 0) return '${days}d ${hours}h';
  if (hours > 0) return '${hours}h ${minutes}min';
  return '${minutes}min';
}
