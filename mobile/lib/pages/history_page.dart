import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../models/air_quality.dart';
import '../models/app_models.dart';
import '../state/app_controller.dart';
import '../widgets/common_widgets.dart';

enum HistoryWindow {
  sixHours('6 h', Duration(hours: 6)),
  day('24 h', Duration(hours: 24)),
  week('7 dias', Duration(days: 7));

  const HistoryWindow(this.label, this.duration);
  final String label;
  final Duration duration;
}

class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key, required this.controller});

  final AppController controller;

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  HistoryWindow _window = HistoryWindow.day;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      widget.controller.loadHistory();
    });
  }

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: widget.controller.loadHistory,
    child: ListView(
      key: const PageStorageKey('history-scroll'),
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(18, 22, 18, 120),
      children: [
        PageHeader(
          title: 'Histórico',
          subtitle: 'Tendências da estação selecionada',
          trailing: widget.controller.historyLoading
              ? const Padding(
                  padding: EdgeInsets.all(10),
                  child: SizedBox.square(
                    dimension: 22,
                    child: CircularProgressIndicator(strokeWidth: 2.5),
                  ),
                )
              : IconButton.filledTonal(
                  onPressed: widget.controller.loadHistory,
                  icon: const Icon(Icons.refresh_rounded),
                ),
        ),
        const SizedBox(height: 18),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SegmentedButton<HistoryWindow>(
            segments: HistoryWindow.values
                .map(
                  (window) =>
                      ButtonSegment(value: window, label: Text(window.label)),
                )
                .toList(growable: false),
            selected: {_window},
            showSelectedIcon: false,
            onSelectionChanged: (selected) {
              setState(() => _window = selected.first);
            },
          ),
        ),
        const SizedBox(height: 16),
        const PrototypeNotice(),
        const SizedBox(height: 20),
        if (_hasNoData)
          SurfaceCard(
            child: EmptyState(
              icon: Icons.query_stats_rounded,
              title: 'Histórico ainda vazio',
              message: widget.controller.health?.persistenceEnabled == false
                  ? 'A persistência do backend está desabilitada. Ative o SQLite para consultar séries após reinícios.'
                  : 'As séries serão exibidas depois que o backend registrar telemetria.',
              action: OutlinedButton.icon(
                onPressed: widget.controller.loadHistory,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Consultar novamente'),
              ),
            ),
          )
        else ...[
          _AnalyticsCard(
            definition: _metric('co2_ppm'),
            points: _filtered('co2_ppm'),
          ),
          const SizedBox(height: 12),
          _AnalyticsCard(
            definition: _metric('pm25_ugm3'),
            points: _filtered('pm25_ugm3'),
          ),
          const SizedBox(height: 12),
          _AnalyticsCard(
            definition: _metric('voc_index'),
            points: _filtered('voc_index'),
          ),
          const SizedBox(height: 12),
          _AnalyticsCard(
            definition: _metric('temperature_c'),
            points: _filtered('temperature_c'),
          ),
          const SizedBox(height: 12),
          _AnalyticsCard(
            definition: _metric('humidity_pct'),
            points: _filtered('humidity_pct'),
          ),
          const SizedBox(height: 18),
          SurfaceCard(
            color: AppPalette.tinted(context, AppPalette.teal),
            borderColor: AppPalette.teal.withValues(alpha: 0.28),
            child: const Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.lightbulb_outline_rounded, color: AppPalette.teal),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Compare picos com ocupação, ventilação e atividades do ambiente. Correlação visual não implica causalidade.',
                    style: TextStyle(height: 1.4),
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    ),
  );

  bool get _hasNoData => widget.controller.history.values.every(
    (points) => points.where((point) => point.value != null).isEmpty,
  );

  List<SeriesPoint> _filtered(String field) {
    final cutoff = DateTime.now().subtract(_window.duration);
    final points = widget.controller.seriesFor(field);
    final result = points
        .where((point) => point.timestamp.isAfter(cutoff))
        .toList();
    return result.isEmpty ? points : result;
  }

  MetricDefinition _metric(String field) =>
      metricDefinitions.firstWhere((metric) => metric.field == field);
}

class _AnalyticsCard extends StatelessWidget {
  const _AnalyticsCard({required this.definition, required this.points});

  final MetricDefinition definition;
  final List<SeriesPoint> points;

  @override
  Widget build(BuildContext context) {
    final values = points
        .map((point) => point.value)
        .whereType<double>()
        .toList();
    final latest = values.isEmpty ? null : values.last;
    final minimum = values.isEmpty
        ? null
        : values.reduce((a, b) => a < b ? a : b);
    final maximum = values.isEmpty
        ? null
        : values.reduce((a, b) => a > b ? a : b);
    final color = colorForLevel(definition.levelFor(latest));
    return SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 39,
                height: 39,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(definition.icon, color: color, size: 21),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      definition.label,
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                    Text(
                      '${points.length} amostras',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppPalette.muted(context),
                      ),
                    ),
                  ],
                ),
              ),
              Text.rich(
                TextSpan(
                  children: [
                    TextSpan(
                      text: definition.format(latest),
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    TextSpan(
                      text: ' ${definition.unit}',
                      style: TextStyle(
                        color: AppPalette.muted(context),
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          SizedBox(
            height: 126,
            width: double.infinity,
            child: MiniLineChart(points: points, color: color, showFill: true),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              _Stat(label: 'Mín.', value: definition.format(minimum)),
              const SizedBox(width: 12),
              _Stat(label: 'Máx.', value: definition.format(maximum)),
              const Spacer(),
              Text(
                definition.reference,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppPalette.muted(context),
                  fontSize: 10.5,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        label,
        style: Theme.of(
          context,
        ).textTheme.bodySmall?.copyWith(color: AppPalette.muted(context)),
      ),
      Text(value, style: const TextStyle(fontWeight: FontWeight.w800)),
    ],
  );
}
