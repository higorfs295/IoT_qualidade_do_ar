import 'package:air_sense/app.dart';
import 'package:air_sense/data/settings_store.dart';
import 'package:air_sense/state/app_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('abre o dashboard completo em modo demonstração', (tester) async {
    final controller = AppController(
      settings: MemorySettingsStore(),
      defaultDemo: true,
    );
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(AirSenseApp(controller: controller));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('Air Sense'), findsOneWidget);
    expect(find.text('Leituras atuais'), findsOneWidget);
    expect(find.text('Ar bom'), findsOneWidget);
    expect(find.byIcon(Icons.dashboard_rounded), findsOneWidget);
  });

  testWidgets('exibe o portal de conexão quando não há configuração', (
    tester,
  ) async {
    final controller = AppController(settings: MemorySettingsStore());

    await tester.pumpWidget(AirSenseApp(controller: controller));
    await tester.pump();

    expect(find.text('Respire informação.'), findsOneWidget);
    expect(find.text('Conectar e continuar'), findsOneWidget);
  });

  testWidgets('navega pelas quatro áreas principais sem erro de layout', (
    tester,
  ) async {
    final controller = AppController(
      settings: MemorySettingsStore(),
      defaultDemo: true,
    );
    tester.view.physicalSize = const Size(500, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(AirSenseApp(controller: controller));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    await tester.tap(find.text('Histórico').last);
    await tester.pump();
    expect(find.text('Tendências da estação selecionada'), findsOneWidget);

    await tester.tap(find.text('Alertas').last);
    await tester.pump();
    expect(find.textContaining('pendentes nesta sessão'), findsOneWidget);

    await tester.tap(find.text('Ajustes').last);
    await tester.pump();
    expect(find.text('Aplicativo, conexão e estação'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
