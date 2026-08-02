import 'package:flutter/material.dart';

import 'app.dart';
import 'data/settings_store.dart';
import 'state/app_controller.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    AirSenseApp(
      controller: AppController(settings: SharedPreferencesSettingsStore()),
    ),
  );
}
