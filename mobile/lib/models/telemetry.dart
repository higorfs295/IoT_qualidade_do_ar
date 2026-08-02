class Measurements {
  const Measurements({
    this.co2Ppm,
    this.vocIndex,
    this.lpgPpm,
    this.pm1,
    this.pm25,
    this.pm10,
    this.temperatureC,
    this.humidityPct,
    this.gasRawV,
  });

  final double? co2Ppm;
  final double? vocIndex;
  final double? lpgPpm;
  final double? pm1;
  final double? pm25;
  final double? pm10;
  final double? temperatureC;
  final double? humidityPct;
  final double? gasRawV;

  factory Measurements.fromJson(Map<String, dynamic> json) => Measurements(
    co2Ppm: _number(json['co2_ppm']),
    vocIndex: _number(json['voc_index'] ?? json['tvoc_ppb']),
    lpgPpm: _number(json['lpg_ppm']),
    pm1: _number(json['pm1_ugm3']),
    pm25: _number(json['pm25_ugm3']),
    pm10: _number(json['pm10_ugm3']),
    temperatureC: _number(json['temperature_c']),
    humidityPct: _number(json['humidity_pct']),
    gasRawV: _number(json['gas_raw_v']),
  );

  double? valueFor(String field) => switch (field) {
    'co2_ppm' => co2Ppm,
    'voc_index' => vocIndex,
    'lpg_ppm' => lpgPpm,
    'pm1_ugm3' => pm1,
    'pm25_ugm3' => pm25,
    'pm10_ugm3' => pm10,
    'temperature_c' => temperatureC,
    'humidity_pct' => humidityPct,
    'gas_raw_v' => gasRawV,
    _ => null,
  };
}

class TelemetryQuality {
  const TelemetryQuality({
    this.gasStatus = 'UNKNOWN',
    this.sensorStatus = 'ERROR',
  });

  final String gasStatus;
  final String sensorStatus;

  factory TelemetryQuality.fromJson(Map<String, dynamic> json) =>
      TelemetryQuality(
        gasStatus: json['gas_status']?.toString().toUpperCase() ?? 'UNKNOWN',
        sensorStatus:
            json['sensor_status']?.toString().toUpperCase() ?? 'ERROR',
      );
}

class TelemetryMetadata {
  const TelemetryMetadata({
    this.firmwareVersion,
    this.bootId,
    this.boardModel,
    this.hardwareRevision,
    this.rssiDbm,
    this.sensorMode,
    this.freeHeapBytes,
    this.minFreeHeapBytes,
    this.maxAllocHeapBytes,
    this.uptimeSeconds,
    this.resetReason,
  });

  final String? firmwareVersion;
  final String? bootId;
  final String? boardModel;
  final String? hardwareRevision;
  final int? rssiDbm;
  final String? sensorMode;
  final int? freeHeapBytes;
  final int? minFreeHeapBytes;
  final int? maxAllocHeapBytes;
  final int? uptimeSeconds;
  final int? resetReason;

  factory TelemetryMetadata.fromJson(Map<String, dynamic> json) =>
      TelemetryMetadata(
        firmwareVersion: json['firmware_version']?.toString(),
        bootId: json['boot_id']?.toString(),
        boardModel: json['board_model']?.toString(),
        hardwareRevision: json['hardware_revision']?.toString(),
        rssiDbm: _integer(json['rssi_dbm']),
        sensorMode: json['sensor_mode']?.toString(),
        freeHeapBytes: _integer(json['free_heap_bytes']),
        minFreeHeapBytes: _integer(json['min_free_heap_bytes']),
        maxAllocHeapBytes: _integer(json['max_alloc_heap_bytes']),
        uptimeSeconds: _integer(json['uptime_s']),
        resetReason: _integer(json['reset_reason']),
      );
}

class Telemetry {
  const Telemetry({
    required this.schemaVersion,
    required this.messageId,
    required this.deviceId,
    required this.siteId,
    required this.sentAt,
    required this.sequence,
    required this.measurements,
    required this.quality,
    required this.metadata,
  });

  final String schemaVersion;
  final String messageId;
  final String deviceId;
  final String siteId;
  final DateTime sentAt;
  final int sequence;
  final Measurements measurements;
  final TelemetryQuality quality;
  final TelemetryMetadata metadata;

  factory Telemetry.fromJson(Map<String, dynamic> json) {
    final measurements = _map(json['measurements']);
    final quality = _map(json['quality']);
    final metadata = _map(json['metadata']);
    return Telemetry(
      schemaVersion: json['schema_version']?.toString() ?? '1.1',
      messageId: json['message_id']?.toString() ?? '',
      deviceId: json['device_id']?.toString() ?? 'desconhecido',
      siteId: json['site_id']?.toString() ?? 'desconhecido',
      sentAt:
          DateTime.tryParse(json['sent_at']?.toString() ?? '')?.toLocal() ??
          DateTime.now(),
      sequence: _integer(json['sequence']) ?? 0,
      measurements: Measurements.fromJson(measurements),
      quality: TelemetryQuality.fromJson(quality),
      metadata: TelemetryMetadata.fromJson(metadata),
    );
  }

  factory Telemetry.demo({int sequence = 1, double phase = 0}) {
    final now = DateTime.now();
    final wobble = (phase % 10) - 5;
    return Telemetry(
      schemaVersion: '1.1',
      messageId: 'DEMO-${now.microsecondsSinceEpoch}',
      deviceId: 'esp32-demo-01',
      siteId: 'ambiente-demonstracao',
      sentAt: now,
      sequence: sequence,
      measurements: Measurements(
        co2Ppm: 690 + wobble * 13,
        vocIndex: 98 + wobble * 2,
        lpgPpm: null,
        pm1: 5 + wobble.abs() * 0.3,
        pm25: 11 + wobble.abs() * 0.8,
        pm10: 18 + wobble.abs(),
        temperatureC: 23.7 + wobble * 0.08,
        humidityPct: 52 + wobble * 0.4,
        gasRawV: 1.12 + wobble * 0.01,
      ),
      quality: const TelemetryQuality(gasStatus: 'SAFE', sensorStatus: 'OK'),
      metadata: const TelemetryMetadata(
        firmwareVersion: 'demo-1.0.0',
        boardModel: 'ESP-WROOM-32 DevKit 30P USB-C',
        hardwareRevision: 'PROTO-REV-A',
        rssiDbm: -57,
        sensorMode: 'HIL',
        freeHeapBytes: 145000,
        minFreeHeapBytes: 121000,
        maxAllocHeapBytes: 92000,
        uptimeSeconds: 8642,
      ),
    );
  }
}

Map<String, dynamic> _map(dynamic value) =>
    value is Map<String, dynamic> ? value : const <String, dynamic>{};

double? _number(dynamic value) => value is num ? value.toDouble() : null;

int? _integer(dynamic value) => value is num ? value.toInt() : null;
