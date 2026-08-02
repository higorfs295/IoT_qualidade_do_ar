import 'package:flutter/material.dart';

import '../state/app_controller.dart';
import '../widgets/common_widgets.dart';
import 'alerts_page.dart';
import 'dashboard_page.dart';
import 'history_page.dart';
import 'settings_page.dart';

class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) => Scaffold(
    body: Column(
      children: [
        ConnectivityBanner(
          restConnected: controller.restConnected,
          wsConnected: controller.wsConnected,
          demoMode: controller.demoMode,
          onRetry: controller.refresh,
        ),
        Expanded(
          child: IndexedStack(
            index: controller.currentTab,
            children: [
              DashboardPage(controller: controller),
              HistoryPage(controller: controller),
              AlertsPage(controller: controller),
              SettingsPage(controller: controller),
            ],
          ),
        ),
      ],
    ),
    bottomNavigationBar: NavigationBar(
      selectedIndex: controller.currentTab,
      onDestinationSelected: controller.setCurrentTab,
      destinations: [
        const NavigationDestination(
          icon: Icon(Icons.dashboard_outlined),
          selectedIcon: Icon(Icons.dashboard_rounded),
          label: 'Agora',
        ),
        const NavigationDestination(
          icon: Icon(Icons.show_chart_rounded),
          selectedIcon: Icon(Icons.monitor_heart_rounded),
          label: 'Histórico',
        ),
        NavigationDestination(
          icon: controller.activeAlerts == 0
              ? const Icon(Icons.notifications_none_rounded)
              : Badge(
                  label: Text('${controller.activeAlerts}'),
                  child: const Icon(Icons.notifications_none_rounded),
                ),
          selectedIcon: const Icon(Icons.notifications_rounded),
          label: 'Alertas',
        ),
        const NavigationDestination(
          icon: Icon(Icons.settings_outlined),
          selectedIcon: Icon(Icons.settings_rounded),
          label: 'Ajustes',
        ),
      ],
    ),
  );
}
