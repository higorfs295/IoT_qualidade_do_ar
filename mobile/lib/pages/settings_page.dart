import 'package:flutter/material.dart';

import '../app.dart';
import '../core/app_theme.dart';
import '../state/app_controller.dart';
import '../widgets/common_widgets.dart';
import 'device_details_page.dart';
import 'hardware_management_page.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key, required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) => ListView(
    key: const PageStorageKey('settings-scroll'),
    padding: const EdgeInsets.fromLTRB(18, 22, 18, 120),
    children: [
      const PageHeader(
        title: 'Ajustes',
        subtitle: 'Aplicativo, conexão e estação',
      ),
      const SizedBox(height: 22),
      const SectionTitle(title: 'Aparência e alertas'),
      const SizedBox(height: 10),
      SurfaceCard(
        padding: EdgeInsets.zero,
        child: Column(
          children: [
            _SettingsTile(
              icon: Icons.palette_outlined,
              title: 'Tema',
              subtitle: _themeLabel(controller.themeMode),
              trailing: DropdownButtonHideUnderline(
                child: DropdownButton<ThemeMode>(
                  value: controller.themeMode,
                  items: const [
                    DropdownMenuItem(
                      value: ThemeMode.system,
                      child: Text('Sistema'),
                    ),
                    DropdownMenuItem(
                      value: ThemeMode.light,
                      child: Text('Claro'),
                    ),
                    DropdownMenuItem(
                      value: ThemeMode.dark,
                      child: Text('Escuro'),
                    ),
                  ],
                  onChanged: (value) {
                    if (value != null) controller.setThemeMode(value);
                  },
                ),
              ),
            ),
            const Divider(height: 1, indent: 58),
            _SettingsTile(
              icon: Icons.notifications_outlined,
              title: 'Alertas na sessão',
              subtitle: 'Gerar eventos a partir das leituras recebidas',
              trailing: Switch(
                value: controller.notificationsEnabled,
                onChanged: controller.setNotificationsEnabled,
              ),
            ),
          ],
        ),
      ),
      const SizedBox(height: 23),
      const SectionTitle(title: 'Estação'),
      const SizedBox(height: 10),
      SurfaceCard(
        padding: EdgeInsets.zero,
        child: Column(
          children: [
            _SettingsTile(
              icon: Icons.memory_rounded,
              title: 'Detalhes do dispositivo',
              subtitle: controller.selectedDeviceId ?? 'Nenhum selecionado',
              onTap: controller.selectedDevice == null
                  ? null
                  : () => _push(
                      context,
                      DeviceDetailsPage(controller: controller),
                    ),
            ),
            const Divider(height: 1, indent: 58),
            _SettingsTile(
              icon: Icons.developer_board_outlined,
              title: 'Hardware e calibração',
              subtitle: 'Sensores, pinagem e checklist técnico',
              onTap: () => _push(
                context,
                HardwareManagementPage(controller: controller),
              ),
            ),
          ],
        ),
      ),
      const SizedBox(height: 23),
      const SectionTitle(title: 'Conexão'),
      const SizedBox(height: 10),
      SurfaceCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.dns_outlined, color: AppPalette.teal),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Backend atual',
                        style: TextStyle(fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        controller.demoMode
                            ? 'Dados de demonstração locais'
                            : controller.baseUrl,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppPalette.muted(context),
                        ),
                      ),
                    ],
                  ),
                ),
                StatusPill(
                  label: controller.demoMode
                      ? 'DEMO'
                      : controller.restConnected
                      ? 'ATIVO'
                      : 'OFFLINE',
                  color: controller.demoMode
                      ? AppPalette.blue
                      : controller.restConnected
                      ? AppPalette.good
                      : AppPalette.danger,
                ),
              ],
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: controller.openConnectionSettings,
              icon: const Icon(Icons.settings_ethernet_rounded),
              label: const Text('Alterar conexão'),
            ),
          ],
        ),
      ),
      const SizedBox(height: 23),
      const SectionTitle(title: 'Sobre'),
      const SizedBox(height: 10),
      const SurfaceCard(
        child: Column(
          children: [
            Row(
              children: [
                BrandMark(size: 46),
                SizedBox(width: 13),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Air Sense Mobile',
                        style: TextStyle(fontWeight: FontWeight.w900),
                      ),
                      SizedBox(height: 2),
                      Text('Versão 1.0.0 • Flutter'),
                    ],
                  ),
                ),
              ],
            ),
            SizedBox(height: 14),
            Text(
              'Cliente móvel do projeto acadêmico IoT de qualidade do ar, preparado para operar com o backend local do repositório.',
              style: TextStyle(height: 1.45),
            ),
          ],
        ),
      ),
    ],
  );

  static String _themeLabel(ThemeMode mode) => switch (mode) {
    ThemeMode.light => 'Claro',
    ThemeMode.dark => 'Escuro',
    ThemeMode.system => 'Acompanha o sistema',
  };

  static void _push(BuildContext context, Widget page) {
    Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => page));
  }
}

class _SettingsTile extends StatelessWidget {
  const _SettingsTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.trailing,
    this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => ListTile(
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
    leading: Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: AppPalette.teal.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Icon(icon, color: AppPalette.teal, size: 21),
    ),
    title: Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
    subtitle: Text(subtitle),
    trailing:
        trailing ??
        (onTap == null ? null : const Icon(Icons.chevron_right_rounded)),
    onTap: onTap,
  );
}
