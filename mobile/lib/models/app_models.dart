import 'telemetry.dart';

class DeviceSummary {
  const DeviceSummary({
    required this.deviceId,
    required this.siteId,
    required this.online,
    this.latest,
  });

  final String deviceId;
  final String siteId;
  final bool online;
  final Telemetry? latest;

  factory DeviceSummary.fromJson(Map<String, dynamic> json) {
    final rawLatest = json['ultimo'];
    return DeviceSummary(
      deviceId: json['device_id']?.toString() ?? 'desconhecido',
      siteId: json['site_id']?.toString() ?? 'desconhecido',
      online: json['online'] == true,
      latest: rawLatest is Map<String, dynamic>
          ? Telemetry.fromJson(rawLatest)
          : null,
    );
  }

  DeviceSummary copyWith({bool? online, Telemetry? latest}) => DeviceSummary(
    deviceId: deviceId,
    siteId: siteId,
    online: online ?? this.online,
    latest: latest ?? this.latest,
  );
}

class ApiHealth {
  const ApiHealth({
    required this.ready,
    required this.mqttEnabled,
    required this.mqttConnected,
    required this.persistenceEnabled,
    required this.devices,
    required this.uptimeSeconds,
    this.persistenceError,
  });

  final bool ready;
  final bool mqttEnabled;
  final bool mqttConnected;
  final bool persistenceEnabled;
  final int devices;
  final int uptimeSeconds;
  final String? persistenceError;

  factory ApiHealth.fromJson(Map<String, dynamic> json) => ApiHealth(
    ready: json['ready'] == true,
    mqttEnabled: json['mqtt_enabled'] == true,
    mqttConnected: json['mqtt_connected'] == true,
    persistenceEnabled: json['persistence_enabled'] == true,
    devices: (json['devices'] as num?)?.toInt() ?? 0,
    uptimeSeconds: (json['uptime_s'] as num?)?.toInt() ?? 0,
    persistenceError: json['persistence_error']?.toString(),
  );
}

class BackendMetrics {
  const BackendMetrics({
    this.received = 0,
    this.invalid = 0,
    this.gaps = 0,
    this.duplicates = 0,
    this.online = 0,
  });

  final int received;
  final int invalid;
  final int gaps;
  final int duplicates;
  final int online;

  factory BackendMetrics.fromJson(Map<String, dynamic> json) => BackendMetrics(
    received: (json['recebidas'] as num?)?.toInt() ?? 0,
    invalid: (json['invalidas'] as num?)?.toInt() ?? 0,
    gaps: (json['lacunas'] as num?)?.toInt() ?? 0,
    duplicates: (json['duplicadas'] as num?)?.toInt() ?? 0,
    online: (json['online'] as num?)?.toInt() ?? 0,
  );
}

class SeriesPoint {
  const SeriesPoint(this.timestamp, this.value);

  final DateTime timestamp;
  final double? value;

  factory SeriesPoint.fromJson(Map<String, dynamic> json) => SeriesPoint(
    DateTime.fromMillisecondsSinceEpoch((json['ts'] as num?)?.toInt() ?? 0),
    json['valor'] is num ? (json['valor'] as num).toDouble() : null,
  );
}

enum AlertSeverity { attention, danger, unavailable }

class AlertEvent {
  const AlertEvent({
    required this.id,
    required this.deviceId,
    required this.title,
    required this.description,
    required this.timestamp,
    required this.severity,
    this.acknowledged = false,
  });

  final String id;
  final String deviceId;
  final String title;
  final String description;
  final DateTime timestamp;
  final AlertSeverity severity;
  final bool acknowledged;

  AlertEvent acknowledge() => AlertEvent(
    id: id,
    deviceId: deviceId,
    title: title,
    description: description,
    timestamp: timestamp,
    severity: severity,
    acknowledged: true,
  );
}
