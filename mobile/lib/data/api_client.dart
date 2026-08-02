import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/app_models.dart';

abstract interface class AirSenseApi {
  Uri get webSocketUri;

  Future<ApiHealth> health();
  Future<BackendMetrics> metrics();
  Future<List<DeviceSummary>> devices();
  Future<List<SeriesPoint>> series(
    String deviceId,
    String field, {
    int limit = 2000,
  });
  void close();
}

class ApiException implements Exception {
  const ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class AirSenseApiClient implements AirSenseApi {
  AirSenseApiClient(String baseUrl, {http.Client? client})
    : _baseUri = normalizeBaseUrl(baseUrl),
      _client = client ?? http.Client();

  final Uri _baseUri;
  final http.Client _client;

  static Uri normalizeBaseUrl(String value) {
    final trimmed = value.trim().replaceFirst(RegExp(r'/+$'), '');
    final uri = Uri.tryParse(trimmed);
    if (uri == null ||
        !uri.hasAuthority ||
        (uri.scheme != 'http' && uri.scheme != 'https')) {
      throw const ApiException(
        'Informe uma URL HTTP válida, por exemplo http://192.168.1.20:3001.',
      );
    }
    return uri;
  }

  @override
  Uri get webSocketUri => _baseUri.replace(
    scheme: _baseUri.scheme == 'https' ? 'wss' : 'ws',
    path: '${_baseUri.path}/ws'.replaceAll(RegExp(r'//+'), '/'),
    query: null,
    fragment: null,
  );

  Uri _uri(String path, [Map<String, dynamic>? query]) {
    final joined = '${_baseUri.path}/$path'.replaceAll(RegExp(r'//+'), '/');
    return _baseUri.replace(
      path: joined,
      queryParameters: query?.map(
        (key, value) => MapEntry(key, value.toString()),
      ),
      fragment: null,
    );
  }

  Future<dynamic> _get(String path, [Map<String, dynamic>? query]) async {
    try {
      final response = await _client
          .get(_uri(path, query), headers: const {'Accept': 'application/json'})
          .timeout(const Duration(seconds: 8));
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException('O servidor respondeu HTTP ${response.statusCode}.');
      }
      return jsonDecode(utf8.decode(response.bodyBytes));
    } on TimeoutException {
      throw const ApiException(
        'O servidor não respondeu dentro de 8 segundos.',
      );
    } on ApiException {
      rethrow;
    } on FormatException {
      throw const ApiException('O servidor retornou JSON inválido.');
    } catch (error) {
      throw ApiException('Não foi possível acessar o backend: $error');
    }
  }

  @override
  Future<ApiHealth> health() async {
    final json = await _get('api/health');
    if (json is! Map<String, dynamic>) {
      throw const ApiException('Resposta inesperada em /api/health.');
    }
    return ApiHealth.fromJson(json);
  }

  @override
  Future<BackendMetrics> metrics() async {
    final json = await _get('api/metricas');
    if (json is! Map<String, dynamic>) {
      throw const ApiException('Resposta inesperada em /api/metricas.');
    }
    return BackendMetrics.fromJson(json);
  }

  @override
  Future<List<DeviceSummary>> devices() async {
    final json = await _get('api/dispositivos');
    if (json is! List) {
      throw const ApiException('Resposta inesperada em /api/dispositivos.');
    }
    return json
        .whereType<Map<String, dynamic>>()
        .map(DeviceSummary.fromJson)
        .toList(growable: false);
  }

  @override
  Future<List<SeriesPoint>> series(
    String deviceId,
    String field, {
    int limit = 2000,
  }) async {
    final safeId = Uri.encodeComponent(deviceId);
    final json = await _get('api/dispositivos/$safeId/serie', {
      'campo': field,
      'n': limit.clamp(1, 5000),
    });
    if (json is! Map<String, dynamic> || json['serie'] is! List) {
      throw const ApiException('Resposta inesperada da série histórica.');
    }
    return (json['serie'] as List)
        .whereType<Map<String, dynamic>>()
        .map(SeriesPoint.fromJson)
        .toList(growable: false);
  }

  @override
  void close() => _client.close();
}
