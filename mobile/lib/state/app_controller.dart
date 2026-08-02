import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../data/api_client.dart';
import '../data/settings_store.dart';
import '../models/air_quality.dart';
import '../models/app_models.dart';
import '../models/telemetry.dart';

typedef ApiFactory = AirSenseApi Function(String baseUrl);

class AppController extends ChangeNotifier {
  AppController({
    required this.settings,
    ApiFactory? apiFactory,
    bool? defaultDemo,
  }) : _apiFactory = apiFactory ?? AirSenseApiClient.new,
       _defaultDemo =
           defaultDemo ??
           const bool.fromEnvironment('AIR_SENSE_DEMO', defaultValue: false),
       baseUrl = _defaultBaseUrl();

  static const _endpointKey = 'api_base_url';
  static const _configuredKey = 'connection_configured';
  static const _demoKey = 'demo_mode';
  static const _themeKey = 'theme_mode';
  static const _notificationsKey = 'notifications_enabled';

  final SettingsStore settings;
  final ApiFactory _apiFactory;
  final bool _defaultDemo;

  bool initialized = false;
  bool configured = false;
  bool connecting = false;
  bool demoMode = false;
  bool restConnected = false;
  bool wsConnected = false;
  bool historyLoading = false;
  String baseUrl;
  String? errorMessage;
  ThemeMode themeMode = ThemeMode.system;
  bool notificationsEnabled = true;
  int currentTab = 0;
  List<DeviceSummary> devices = const [];
  String? selectedDeviceId;
  Telemetry? currentTelemetry;
  ApiHealth? health;
  BackendMetrics backendMetrics = const BackendMetrics();
  Map<String, List<SeriesPoint>> history = const {};
  List<AlertEvent> alerts = const [];

  AirSenseApi? _api;
  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _webSocketSubscription;
  Timer? _pollTimer;
  Timer? _demoTimer;
  Timer? _reconnectTimer;
  int _reconnectAttempt = 0;
  int _demoSequence = 0;
  bool _disposed = false;
  final Map<String, DateTime> _alertCooldown = {};

  static String _defaultBaseUrl() {
    const defined = String.fromEnvironment('API_BASE_URL');
    if (defined.isNotEmpty) return defined;
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:3001';
    }
    return 'http://localhost:3001';
  }

  DeviceSummary? get selectedDevice {
    for (final device in devices) {
      if (device.deviceId == selectedDeviceId) return device;
    }
    return devices.isEmpty ? null : devices.first;
  }

  int get activeAlerts => alerts.where((alert) => !alert.acknowledged).length;

  Future<void> initialize() async {
    try {
      baseUrl = await settings.getString(_endpointKey) ?? baseUrl;
      notificationsEnabled = await settings.getBool(_notificationsKey) ?? true;
      themeMode = _themeFromValue(await settings.getString(_themeKey));
      final savedDemo = await settings.getBool(_demoKey) ?? false;
      final savedConfigured = await settings.getBool(_configuredKey) ?? false;

      initialized = true;
      _notify();
      if (_defaultDemo || savedDemo) {
        await startDemo(persist: _defaultDemo || savedDemo);
      } else if (savedConfigured) {
        await connect(baseUrl, persist: false);
      }
    } catch (error) {
      initialized = true;
      configured = false;
      errorMessage = 'Não foi possível carregar as preferências: $error';
      _notify();
    }
  }

  Future<bool> connect(String endpoint, {bool persist = true}) async {
    if (connecting) return false;
    connecting = true;
    errorMessage = null;
    _notify();
    await _stopDataSources();

    try {
      final normalized = AirSenseApiClient.normalizeBaseUrl(
        endpoint,
      ).toString();
      final api = _apiFactory(normalized);
      _api = api;
      final results = await Future.wait<dynamic>([
        api.health(),
        api.devices(),
        api.metrics(),
      ]);

      baseUrl = normalized;
      health = results[0] as ApiHealth;
      devices = results[1] as List<DeviceSummary>;
      backendMetrics = results[2] as BackendMetrics;
      demoMode = false;
      restConnected = true;
      configured = true;
      selectedDeviceId = _validSelectedDevice(selectedDeviceId);
      currentTelemetry = selectedDevice?.latest;
      connecting = false;
      if (persist) await _saveConnection(demo: false);
      _startPolling();
      unawaited(_startWebSocket());
      _notify();
      return true;
    } catch (error) {
      _api?.close();
      _api = null;
      configured = false;
      restConnected = false;
      wsConnected = false;
      connecting = false;
      errorMessage = error is ApiException ? error.message : error.toString();
      _notify();
      return false;
    }
  }

  Future<void> startDemo({bool persist = true}) async {
    await _stopDataSources();
    demoMode = true;
    configured = true;
    restConnected = true;
    wsConnected = true;
    connecting = false;
    errorMessage = null;
    _demoSequence = math.max(_demoSequence, 1);
    final telemetry = Telemetry.demo(sequence: _demoSequence);
    selectedDeviceId = telemetry.deviceId;
    devices = [
      DeviceSummary(
        deviceId: telemetry.deviceId,
        siteId: telemetry.siteId,
        online: true,
        latest: telemetry,
      ),
    ];
    health = const ApiHealth(
      ready: true,
      mqttEnabled: true,
      mqttConnected: true,
      persistenceEnabled: true,
      devices: 1,
      uptimeSeconds: 8642,
    );
    backendMetrics = const BackendMetrics(received: 18240, online: 1);
    history = _buildDemoHistory();
    currentTelemetry = telemetry;
    if (alerts.isEmpty) {
      alerts = [
        AlertEvent(
          id: 'demo-active',
          deviceId: telemetry.deviceId,
          title: 'Atenção',
          description:
              'O CO₂ ultrapassou a faixa operacional por alguns minutos.',
          timestamp: DateTime.now().subtract(const Duration(minutes: 18)),
          severity: AlertSeverity.attention,
        ),
        AlertEvent(
          id: 'demo-acknowledged',
          deviceId: telemetry.deviceId,
          title: 'Sensor temporariamente indisponível',
          description:
              'Uma amostra inválida foi descartada sem interromper o fluxo.',
          timestamp: DateTime.now().subtract(const Duration(hours: 5)),
          severity: AlertSeverity.unavailable,
          acknowledged: true,
        ),
      ];
    }
    _demoTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      _demoSequence++;
      _registerTelemetry(
        Telemetry.demo(sequence: _demoSequence, phase: _demoSequence / 2),
      );
    });
    if (persist) await _saveConnection(demo: true);
    _notify();
  }

  Future<void> openConnectionSettings() async {
    await _stopDataSources();
    configured = false;
    restConnected = false;
    wsConnected = false;
    demoMode = false;
    await settings.setBool(_configuredKey, false);
    await settings.setBool(_demoKey, false);
    _notify();
  }

  Future<void> refresh() async {
    if (demoMode) {
      _demoSequence++;
      _registerTelemetry(
        Telemetry.demo(sequence: _demoSequence, phase: _demoSequence / 2),
      );
      return;
    }
    final api = _api;
    if (api == null) return;
    try {
      final results = await Future.wait<dynamic>([
        api.health(),
        api.devices(),
        api.metrics(),
      ]);
      health = results[0] as ApiHealth;
      devices = results[1] as List<DeviceSummary>;
      backendMetrics = results[2] as BackendMetrics;
      selectedDeviceId = _validSelectedDevice(selectedDeviceId);
      currentTelemetry = selectedDevice?.latest ?? currentTelemetry;
      restConnected = true;
      errorMessage = null;
    } catch (error) {
      restConnected = false;
      errorMessage = error is ApiException ? error.message : error.toString();
    }
    _notify();
  }

  Future<void> loadHistory({int limit = 2000}) async {
    if (demoMode || historyLoading) return;
    final api = _api;
    final deviceId = selectedDeviceId;
    if (api == null || deviceId == null) return;
    historyLoading = true;
    _notify();
    try {
      const fields = [
        'co2_ppm',
        'pm25_ugm3',
        'pm10_ugm3',
        'voc_index',
        'temperature_c',
        'humidity_pct',
      ];
      final values = await Future.wait(
        fields.map((field) => api.series(deviceId, field, limit: limit)),
      );
      history = {
        for (var index = 0; index < fields.length; index++)
          fields[index]: values[index],
      };
      errorMessage = null;
    } catch (error) {
      errorMessage = error is ApiException ? error.message : error.toString();
    } finally {
      historyLoading = false;
      _notify();
    }
  }

  List<SeriesPoint> seriesFor(String field) => history[field] ?? const [];

  void selectDevice(String? deviceId) {
    if (deviceId == null || deviceId == selectedDeviceId) return;
    selectedDeviceId = deviceId;
    currentTelemetry = selectedDevice?.latest;
    history = const {};
    _notify();
    unawaited(loadHistory());
  }

  void setCurrentTab(int value) {
    currentTab = value.clamp(0, 3);
    _notify();
  }

  Future<void> setThemeMode(ThemeMode value) async {
    themeMode = value;
    await settings.setString(_themeKey, value.name);
    _notify();
  }

  Future<void> setNotificationsEnabled(bool value) async {
    notificationsEnabled = value;
    await settings.setBool(_notificationsKey, value);
    _notify();
  }

  void acknowledgeAlert(String id) {
    alerts = [
      for (final alert in alerts)
        if (alert.id == id) alert.acknowledge() else alert,
    ];
    _notify();
  }

  void acknowledgeAll() {
    alerts = alerts.map((alert) => alert.acknowledge()).toList(growable: false);
    _notify();
  }

  Future<void> _saveConnection({required bool demo}) async {
    await settings.setString(_endpointKey, baseUrl);
    await settings.setBool(_configuredKey, true);
    await settings.setBool(_demoKey, demo);
  }

  String? _validSelectedDevice(String? current) {
    if (devices.any((device) => device.deviceId == current)) return current;
    return devices.isEmpty ? null : devices.first.deviceId;
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => unawaited(refresh()),
    );
  }

  Future<void> _startWebSocket() async {
    final api = _api;
    if (api == null || demoMode || _disposed) return;
    try {
      final channel = WebSocketChannel.connect(api.webSocketUri);
      _channel = channel;
      await channel.ready.timeout(const Duration(seconds: 8));
      if (_disposed || _api != api) {
        await channel.sink.close();
        return;
      }
      wsConnected = true;
      _reconnectAttempt = 0;
      _notify();
      _webSocketSubscription = channel.stream.listen(
        _handleWebSocketMessage,
        onError: (_) => _handleWebSocketClosed(),
        onDone: _handleWebSocketClosed,
        cancelOnError: true,
      );
    } catch (_) {
      _handleWebSocketClosed();
    }
  }

  void _handleWebSocketMessage(dynamic raw) {
    try {
      final json = jsonDecode(raw.toString());
      if (json is Map<String, dynamic> &&
          (json['tipo'] == 'telemetria' || json['tipo'] == 'telemetry')) {
        final data = json['msg'] ?? json['dados'];
        if (data is Map<String, dynamic>) {
          _registerTelemetry(Telemetry.fromJson(data));
        }
      }
    } catch (_) {
      // Uma mensagem inválida é ignorada sem interromper o fluxo válido.
    }
  }

  void _handleWebSocketClosed() {
    if (_disposed || demoMode || _api == null) return;
    wsConnected = false;
    _notify();
    _reconnectTimer?.cancel();
    const delays = [2, 4, 8, 16, 30];
    final seconds = delays[_reconnectAttempt.clamp(0, delays.length - 1)];
    _reconnectAttempt++;
    _reconnectTimer = Timer(
      Duration(seconds: seconds),
      () => unawaited(_startWebSocket()),
    );
  }

  void _registerTelemetry(Telemetry telemetry) {
    final index = devices.indexWhere(
      (device) => device.deviceId == telemetry.deviceId,
    );
    final updated = [...devices];
    if (index < 0) {
      updated.add(
        DeviceSummary(
          deviceId: telemetry.deviceId,
          siteId: telemetry.siteId,
          online: true,
          latest: telemetry,
        ),
      );
    } else {
      updated[index] = updated[index].copyWith(online: true, latest: telemetry);
    }
    devices = updated;
    selectedDeviceId ??= telemetry.deviceId;
    if (selectedDeviceId == telemetry.deviceId) {
      currentTelemetry = telemetry;
      final updatedHistory = <String, List<SeriesPoint>>{...history};
      for (final metric in metricDefinitions) {
        final points = <SeriesPoint>[
          ...(updatedHistory[metric.field] ?? const []),
        ];
        points.add(
          SeriesPoint(
            telemetry.sentAt,
            telemetry.measurements.valueFor(metric.field),
          ),
        );
        if (points.length > 2000) points.removeRange(0, points.length - 2000);
        updatedHistory[metric.field] = points;
      }
      history = updatedHistory;
      _considerAlert(telemetry);
    }
    backendMetrics = BackendMetrics(
      received: backendMetrics.received + 1,
      invalid: backendMetrics.invalid,
      gaps: backendMetrics.gaps,
      duplicates: backendMetrics.duplicates,
      online: devices.where((device) => device.online).length,
    );
    _notify();
  }

  void _considerAlert(Telemetry telemetry) {
    if (!notificationsEnabled) return;
    final verdict = verdictFor(telemetry);
    if (verdict.level == AirLevel.good) return;
    final key = '${telemetry.deviceId}:${verdict.level.name}';
    final now = DateTime.now();
    final previous = _alertCooldown[key];
    if (previous != null &&
        now.difference(previous) < const Duration(minutes: 10)) {
      return;
    }
    _alertCooldown[key] = now;
    final severity = switch (verdict.level) {
      AirLevel.danger => AlertSeverity.danger,
      AirLevel.attention => AlertSeverity.attention,
      _ => AlertSeverity.unavailable,
    };
    alerts = [
      AlertEvent(
        id: '${telemetry.deviceId}-${now.microsecondsSinceEpoch}',
        deviceId: telemetry.deviceId,
        title: verdict.title,
        description: verdict.description,
        timestamp: telemetry.sentAt,
        severity: severity,
      ),
      ...alerts,
    ].take(100).toList(growable: false);
  }

  Map<String, List<SeriesPoint>> _buildDemoHistory() {
    final random = math.Random(42);
    final now = DateTime.now();
    final result = <String, List<SeriesPoint>>{
      for (final metric in metricDefinitions) metric.field: <SeriesPoint>[],
    };
    for (var index = 95; index >= 0; index--) {
      final time = now.subtract(Duration(minutes: index * 15));
      final wave = math.sin((95 - index) / 7);
      final values = <String, double>{
        'co2_ppm': 680 + wave * 95 + random.nextDouble() * 20,
        'pm25_ugm3': 12 + wave * 4 + random.nextDouble() * 2,
        'pm10_ugm3': 20 + wave * 6 + random.nextDouble() * 3,
        'voc_index': 100 + wave * 22 + random.nextDouble() * 8,
        'temperature_c': 23.5 + wave * 1.3,
        'humidity_pct': 51 - wave * 5,
        'pm1_ugm3': 7 + wave * 2,
        'gas_raw_v': 1.1 + wave * 0.05,
      };
      for (final entry in values.entries) {
        result[entry.key]!.add(SeriesPoint(time, entry.value));
      }
    }
    return result;
  }

  Future<void> _stopDataSources() async {
    _pollTimer?.cancel();
    _demoTimer?.cancel();
    _reconnectTimer?.cancel();
    await _webSocketSubscription?.cancel();
    _webSocketSubscription = null;
    await _channel?.sink.close();
    _channel = null;
    _api?.close();
    _api = null;
    wsConnected = false;
  }

  ThemeMode _themeFromValue(String? value) => switch (value) {
    'light' => ThemeMode.light,
    'dark' => ThemeMode.dark,
    _ => ThemeMode.system,
  };

  void _notify() {
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _pollTimer?.cancel();
    _demoTimer?.cancel();
    _reconnectTimer?.cancel();
    unawaited(_webSocketSubscription?.cancel());
    unawaited(_channel?.sink.close());
    _api?.close();
    super.dispose();
  }
}
