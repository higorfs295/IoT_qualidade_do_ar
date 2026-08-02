import 'package:air_sense/models/air_quality.dart';
import 'package:air_sense/models/telemetry.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('classifica uma amostra saudável como boa', () {
    final telemetry = Telemetry.demo();

    expect(verdictFor(telemetry).level, AirLevel.good);
  });

  test('prioriza gas_status inseguro como perigo', () {
    final telemetry = Telemetry.fromJson({
      'device_id': 'esp32-01',
      'site_id': 'laboratorio',
      'sent_at': '2026-08-02T12:00:00Z',
      'sequence': 10,
      'measurements': {'co2_ppm': 500},
      'quality': {'gas_status': 'UNSAFE', 'sensor_status': 'OK'},
    });

    expect(verdictFor(telemetry).level, AirLevel.danger);
  });

  test('marca CO2 acima de 800 ppm como atenção', () {
    final co2 = metricDefinitions.firstWhere(
      (metric) => metric.field == 'co2_ppm',
    );

    expect(co2.levelFor(799), AirLevel.good);
    expect(co2.levelFor(800), AirLevel.attention);
    expect(co2.levelFor(1000), AirLevel.danger);
  });
}
