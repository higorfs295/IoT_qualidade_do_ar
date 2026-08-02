/* config.js — configuracao do painel.
 * MODO: 'auto' tenta o backend real e mostra demo identificada se ele falhar;
 *       'live' forca o backend; 'mock' simula no navegador (bom p/ demonstrar).
 * (herda a ideia do config.js do IoT-IDEA)
 */
window.APP_CONFIG = {
  MODO: "auto",
  BASE_URL: "",       // '' = mesma origem (servido pelo backend)
  WS_PATH: "/ws",
  MOCK_TICK_MS: 2000, // ritmo da simulacao no modo mock
};
