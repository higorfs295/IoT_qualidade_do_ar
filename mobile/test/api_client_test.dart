import 'dart:convert';

import 'package:air_sense/data/api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('normaliza REST e deriva a URL do WebSocket', () {
    final api = AirSenseApiClient(
      'https://air.example.com/base/',
      client: MockClient((_) async => http.Response('{}', 200)),
    );

    expect(api.webSocketUri.toString(), 'wss://air.example.com/base/ws');
    api.close();
  });

  test('consulta e converte a lista de dispositivos', () async {
    final client = MockClient((request) async {
      expect(request.url.path, '/api/dispositivos');
      return http.Response.bytes(
        utf8.encode(
          jsonEncode([
            {
              'device_id': 'esp32-01',
              'site_id': 'lab',
              'online': true,
              'ultimo': {
                'device_id': 'esp32-01',
                'site_id': 'lab',
                'sent_at': '2026-08-02T12:00:00Z',
                'sequence': 1,
                'measurements': {'co2_ppm': 640},
                'quality': {'gas_status': 'SAFE', 'sensor_status': 'OK'},
              },
            },
          ]),
        ),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final api = AirSenseApiClient('http://localhost:3001', client: client);

    final devices = await api.devices();

    expect(devices, hasLength(1));
    expect(devices.single.deviceId, 'esp32-01');
    expect(devices.single.latest?.measurements.co2Ppm, 640);
    api.close();
  });
}
