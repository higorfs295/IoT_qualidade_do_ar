import 'package:flutter/material.dart';

import '../app.dart';
import '../core/app_theme.dart';
import '../state/app_controller.dart';
import '../widgets/common_widgets.dart';

class ConnectionPage extends StatefulWidget {
  const ConnectionPage({super.key, required this.controller});

  final AppController controller;

  @override
  State<ConnectionPage> createState() => _ConnectionPageState();
}

class _ConnectionPageState extends State<ConnectionPage> {
  late final TextEditingController _endpointController;

  @override
  void initState() {
    super.initState();
    _endpointController = TextEditingController(
      text: widget.controller.baseUrl,
    );
  }

  @override
  void dispose() {
    _endpointController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Align(
                  alignment: Alignment.centerLeft,
                  child: BrandMark(size: 68),
                ),
                const SizedBox(height: 27),
                Text(
                  'Respire informação.',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: AppPalette.navy,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -1.2,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Conecte o Air Sense ao backend local para acompanhar a estação ESP32 em tempo real.',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: AppPalette.muted(context),
                    height: 1.45,
                  ),
                ),
                const SizedBox(height: 28),
                SurfaceCard(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Conexão com a API',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        'A URL fica salva somente neste dispositivo.',
                        style: TextStyle(color: AppPalette.muted(context)),
                      ),
                      const SizedBox(height: 18),
                      TextField(
                        controller: _endpointController,
                        keyboardType: TextInputType.url,
                        textInputAction: TextInputAction.done,
                        autocorrect: false,
                        enableSuggestions: false,
                        onSubmitted: (_) => _connect(),
                        decoration: const InputDecoration(
                          labelText: 'URL do backend',
                          hintText: 'http://192.168.1.20:3001',
                          prefixIcon: Icon(Icons.dns_outlined),
                        ),
                      ),
                      if (widget.controller.errorMessage != null) ...[
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppPalette.danger.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            widget.controller.errorMessage!,
                            style: const TextStyle(
                              color: AppPalette.danger,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                      const SizedBox(height: 16),
                      FilledButton.icon(
                        onPressed: widget.controller.connecting
                            ? null
                            : _connect,
                        icon: widget.controller.connecting
                            ? const SizedBox.square(
                                dimension: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.link_rounded),
                        label: Text(
                          widget.controller.connecting
                              ? 'Verificando…'
                              : 'Conectar e continuar',
                        ),
                      ),
                      const SizedBox(height: 10),
                      OutlinedButton.icon(
                        onPressed: widget.controller.connecting
                            ? null
                            : () => widget.controller.startDemo(),
                        icon: const Icon(Icons.science_outlined),
                        label: const Text('Explorar com dados de demonstração'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                SurfaceCard(
                  padding: const EdgeInsets.all(16),
                  color: AppPalette.tinted(context, AppPalette.blue),
                  borderColor: AppPalette.blue.withValues(alpha: 0.25),
                  child: const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Como encontrar a URL',
                        style: TextStyle(fontWeight: FontWeight.w800),
                      ),
                      SizedBox(height: 8),
                      Text(
                        '• Android Emulator: http://10.0.2.2:3001\n'
                        '• Celular físico: use o IP do computador na mesma rede Wi-Fi\n'
                        '• iPhone Simulator/Web: http://localhost:3001',
                        style: TextStyle(height: 1.55),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  'Air Sense • monitoramento IoT acadêmico',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppPalette.muted(context),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );

  Future<void> _connect() async {
    FocusManager.instance.primaryFocus?.unfocus();
    await widget.controller.connect(_endpointController.text);
  }
}
