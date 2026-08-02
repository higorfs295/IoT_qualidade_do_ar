import 'package:flutter/material.dart';

abstract final class AppPalette {
  static const navy = Color(0xFF12324A);
  static const teal = Color(0xFF147D72);
  static const blue = Color(0xFF2563EB);
  static const good = Color(0xFF16A34A);
  static const attention = Color(0xFFD97706);
  static const danger = Color(0xFFDC2626);
  static const neutral = Color(0xFF64748B);

  static const lightBackground = Color(0xFFF4F6F8);
  static const lightSurface = Colors.white;
  static const lightText = Color(0xFF1A2230);
  static const lightMuted = Color(0xFF5B6673);
  static const lightBorder = Color(0xFFE3E8EE);

  static const darkBackground = Color(0xFF0F141B);
  static const darkSurface = Color(0xFF1A212B);
  static const darkText = Color(0xFFE8EDF3);
  static const darkMuted = Color(0xFF9AA7B6);
  static const darkBorder = Color(0xFF2A333F);

  static Color surface(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark
      ? darkSurface
      : lightSurface;

  static Color muted(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark ? darkMuted : lightMuted;

  static Color border(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark
      ? darkBorder
      : lightBorder;

  static Color tinted(BuildContext context, Color color) =>
      Color.alphaBlend(color.withValues(alpha: 0.12), surface(context));
}

abstract final class AppTheme {
  static ThemeData light() => _build(Brightness.light);
  static ThemeData dark() => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final dark = brightness == Brightness.dark;
    final scheme = ColorScheme.fromSeed(
      seedColor: AppPalette.teal,
      brightness: brightness,
      primary: AppPalette.teal,
      secondary: AppPalette.blue,
      error: AppPalette.danger,
      surface: dark ? AppPalette.darkSurface : AppPalette.lightSurface,
    );
    final textColor = dark ? AppPalette.darkText : AppPalette.lightText;
    final border = dark ? AppPalette.darkBorder : AppPalette.lightBorder;

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: dark
          ? AppPalette.darkBackground
          : AppPalette.lightBackground,
      splashFactory: InkSparkle.splashFactory,
      textTheme: ThemeData(
        brightness: brightness,
      ).textTheme.apply(bodyColor: textColor, displayColor: textColor),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.transparent,
        foregroundColor: textColor,
        centerTitle: false,
        elevation: 0,
        scrolledUnderElevation: 0,
        titleTextStyle: TextStyle(
          color: textColor,
          fontSize: 21,
          fontWeight: FontWeight.w800,
          letterSpacing: -0.4,
        ),
      ),
      dividerColor: border,
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: dark ? AppPalette.darkSurface : Colors.white,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 15,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppPalette.teal, width: 2),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppPalette.teal,
          foregroundColor: Colors.white,
          minimumSize: const Size(48, 52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(fontWeight: FontWeight.w700),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(48, 50),
          foregroundColor: textColor,
          side: BorderSide(color: border),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(fontWeight: FontWeight.w700),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: dark ? AppPalette.darkSurface : Colors.white,
        selectedColor: AppPalette.teal.withValues(alpha: 0.18),
        side: BorderSide(color: border),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
        labelStyle: TextStyle(color: textColor, fontWeight: FontWeight.w600),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 70,
        backgroundColor: dark ? AppPalette.darkSurface : Colors.white,
        indicatorColor: AppPalette.teal.withValues(alpha: 0.18),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          return TextStyle(
            fontSize: 12,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w800
                : FontWeight.w600,
          );
        }),
      ),
    );
  }
}
