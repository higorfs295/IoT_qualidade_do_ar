import 'package:air_sense/models/telemetry.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('interpreta o contrato de telemetria 1.1', () {
    final telemetry = Telemetry.fromJson({
      'schema_version': '1.1',
      'message_id': '01JTEST0000000000000000000',
      'device_id': 'esp32-lab-01',
      'site_id': 'lab-iot',
      'sent_at': '2026-08-02T12:30:00Z',
      'sequence': 123,
      'measurements': {
        'co2_ppm': 712,
        'pm25_ugm3': 10.4,
        'temperature_c': 23.8,
      },
      'quality': {'gas_status': 'SAFE', 'sensor_status': 'OK'},
      'metadata': {
        'firmware_version': '1.0.0',
        'board_model': 'ESP-WROOM-32',
        'free_heap_bytes': 140000,
      },
    });

    expect(telemetry.deviceId, 'esp32-lab-01');
    expect(telemetry.sequence, 123);
    expect(telemetry.measurements.co2Ppm, 712);
    expect(telemetry.measurements.pm25, 10.4);
    expect(telemetry.quality.gasStatus, 'SAFE');
    expect(telemetry.metadata.freeHeapBytes, 140000);
  });

  test('mantém campos opcionais ausentes como nulos', () {
    final telemetry = Telemetry.fromJson(const {});

    expect(telemetry.measurements.co2Ppm, isNull);
    expect(telemetry.metadata.rssiDbm, isNull);
    expect(telemetry.quality.sensorStatus, 'ERROR');
  });
}
