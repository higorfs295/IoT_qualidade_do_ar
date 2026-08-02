import 'package:flutter/material.dart';

import 'core/app_theme.dart';
import 'pages/app_shell.dart';
import 'pages/connection_page.dart';
import 'state/app_controller.dart';

class AirSenseApp extends StatefulWidget {
  const AirSenseApp({super.key, required this.controller});

  final AppController controller;

  @override
  State<AirSenseApp> createState() => _AirSenseAppState();
}

class _AirSenseAppState extends State<AirSenseApp> {
  @override
  void initState() {
    super.initState();
    widget.controller.initialize();
  }

  @override
  void dispose() {
    widget.controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: widget.controller,
    builder: (context, _) => MaterialApp(
      title: 'Air Sense',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: widget.controller.themeMode,
      home: !widget.controller.initialized
          ? const _SplashPage()
          : widget.controller.configured
          ? AppShell(controller: widget.controller)
          : ConnectionPage(controller: widget.controller),
    ),
  );
}

class _SplashPage extends StatelessWidget {
  const _SplashPage();

  @override
  Widget build(BuildContext context) => const Scaffold(
    body: Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _BrandMark(size: 74),
          SizedBox(height: 22),
          CircularProgressIndicator(),
        ],
      ),
    ),
  );
}

class BrandMark extends StatelessWidget {
  const BrandMark({super.key, this.size = 54});

  final double size;

  @override
  Widget build(BuildContext context) => _BrandMark(size: size);
}

class _BrandMark extends StatelessWidget {
  const _BrandMark({required this.size});

  final double size;

  @override
  Widget build(BuildContext context) => Container(
    width: size,
    height: size,
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [AppPalette.navy, AppPalette.teal],
      ),
      borderRadius: BorderRadius.circular(size * 0.29),
      boxShadow: [
        BoxShadow(
          color: AppPalette.teal.withValues(alpha: 0.25),
          blurRadius: 24,
          offset: const Offset(0, 9),
        ),
      ],
    ),
    child: Icon(Icons.air_rounded, size: size * 0.56, color: Colors.white),
  );
}
