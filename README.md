# Фото с Дедом Морозом

Веб-сайт для съёмки фото ребёнка с Дедом Морозом и Снегурочкой. Три режима:

- **Простой режим** (`simple.html`) — работает на всех устройствах.
- **AR WebXR** (`ar.html`) — настоящий AR с окклюзией (Chrome на Android).
- **AR 8th Wall** (`ar-8thwall.html`) — AR через 8th Wall (iOS Safari + Android Chrome).

## Структура проекта

```
index.html         — экран выбора режима (3 кнопки)
simple.html        — простой режим (PNG поверх камеры)
ar.html            — AR через WebXR (Chrome Android, с окклюзией)
ar-8thwall.html    — AR через 8th Wall (iOS + Android, без окклюзии)
santa.png          — изображение (прозрачный фон)
santa.usdz         — 3D-модель для iOS Quick Look (опционально)
xr.js              — движок 8th Wall (~1 MB)
xr-slam.js         — SLAM-модуль 8th Wall (~5 MB)
resources/         — вспомогательные файлы движка
```

## Локальный запуск

```bash
python3 -m http.server 8080
```

Откройте: http://localhost:8080

## Деплой на Vercel

1. Откройте ссылку (нужен аккаунт Vercel, можно войти через GitHub):
   **https://vercel.com/new/import?repository-url=https://github.com/VictorChe/foto-dedmoroz**
2. Нажмите **Import** → **Deploy**.
3. Через 1–2 минуты сайт будет доступен по ссылке вида `https://foto-dedmoroz-xxx.vercel.app`. После этого каждый пуш в `main` будет автоматически выкатываться на Vercel.

Через CLI: `npx vercel` из папки проекта (предварительно `npx vercel login`).

## Какой режим для какого устройства

| Режим | Android Chrome | iOS Safari |
|-------|---------------|------------|
| Простой | Да | Да |
| AR WebXR | Да (с окклюзией) | Нет |
| AR 8th Wall | Да | Да (без окклюзии) |
