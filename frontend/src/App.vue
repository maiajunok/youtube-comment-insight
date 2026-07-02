<template>
  <AppLayout />
</template>

<script setup lang="ts">
import AppLayout from '@/layouts/AppLayout.vue'
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', sans-serif;
  height: 100vh;
}

#app { width: 100%; height: 100vh; }

.shell { display: flex; height: 100vh; overflow: hidden; }

/* ── 사이드바 ── */
.sidebar {
  width: 210px;
  flex-shrink: 0;
  background: var(--sidebar-bg);
  border-right: 0.5px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  padding: 0 0 20px;
  transition: background 0.2s;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 60px;
  box-sizing: border-box;
  padding: 0 18px;
  border-bottom: 0.5px solid var(--sidebar-border);
  margin-bottom: 14px;
  flex-shrink: 0;
}
.logo-icon {
  width: 30px; height: 30px;
  border-radius: 8px;
  background: rgb(from var(--accent) r g b / 0.12);
  border: 0.5px solid rgb(from var(--accent) r g b / 0.4);
  display: flex; align-items: center; justify-content: center;
  color: var(--accent);
}
.logo-text { font-size: 14px; font-weight: 600; color: var(--text); }

.nav-section {
  font-size: 10px;
  letter-spacing: .1em;
  color: var(--dim);
  padding: 0 18px 8px;
  text-transform: uppercase;
  font-weight: 600;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 18px;
  font-size: 13px;
  font-weight: 400;
  color: var(--subtext);
  cursor: pointer;
  border-left: 2px solid transparent;
  transition: color .15s, background .15s;
  user-select: none;
}
.nav-item:hover { color: var(--text); background: var(--card-hover); }
.nav-item.active {
  color: var(--accent);
  background: rgb(from var(--accent) r g b / 0.08);
  border-left-color: var(--accent);
}
.nav-icon { width: 16px; height: 16px; flex-shrink: 0; }

.github-link { text-decoration: none; }

.analyzing-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--accent);
  margin-left: auto;
  flex-shrink: 0;
  animation: dot-pulse 1.4s ease-in-out infinite;
}
@keyframes dot-pulse {
  0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 6px 1px var(--accent); }
  50%       { opacity: 0.35; transform: scale(0.7); box-shadow: 0 0 2px 0 var(--accent); }
}

.done-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--positive);
  margin-left: auto;
  flex-shrink: 0;
  box-shadow: 0 0 6px 1px var(--positive);
  animation: done-appear 0.4s ease-out;
}
@keyframes done-appear {
  from { opacity: 0; transform: scale(0.4); }
  to   { opacity: 1; transform: scale(1); }
}

.nav-divider { height: 0.5px; background: var(--sidebar-border); margin: 10px 0; }

.nav-bottom {
  margin-top: auto;
  padding-top: 10px;
  border-top: 0.5px solid var(--sidebar-border);
}

/* ── 메인 ── */
.main {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: var(--bg);
  display: flex;
  flex-direction: column;
  transition: background 0.2s;
}

/* ── 움직이는 orb 배경 ── */
.orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
  filter: blur(130px);
}

.orb-1 {
  width: 620px; height: 520px;
  background: rgb(from var(--accent) r g b / 0.12);
  top: -100px; right: 3%;
  animation: orb-drift-1 8s ease-in-out infinite;
}

.orb-2 {
  width: 480px; height: 540px;
  background: rgb(from var(--accent) r g b / 0.1);
  bottom: -80px; left: 0%;
  animation: orb-drift-2 10s ease-in-out infinite;
}

.orb-3 {
  width: 340px; height: 340px;
  background: rgb(from var(--accent) r g b / 0.06);
  top: 35%; left: 38%;
  animation: orb-drift-3 12s ease-in-out infinite;
}

[data-theme="light"] .orb-1 { background: rgb(from var(--accent) r g b / 0.06); }
[data-theme="light"] .orb-2 { background: rgb(from var(--accent) r g b / 0.05); }
[data-theme="light"] .orb-3 { background: rgb(from var(--accent) r g b / 0.03); }

@keyframes orb-drift-1 {
  0%,  100% { transform: translate(0px,    0px)   scale(1);    }
  33%        { transform: translate(-70px,  55px)  scale(1.08); }
  66%        { transform: translate(50px,  -45px)  scale(0.92); }
}

@keyframes orb-drift-2 {
  0%,  100% { transform: translate(0px,   0px)   scale(1);    }
  40%        { transform: translate(80px, -60px)  scale(1.10); }
  75%        { transform: translate(-40px, 45px)  scale(0.93); }
}

@keyframes orb-drift-3 {
  0%,  100% { transform: translate(0px,   0px)   scale(1);    }
  35%        { transform: translate(-55px, 65px)  scale(1.15); }
  70%        { transform: translate(60px, -50px)  scale(0.88); }
}

/* ── 탑바 ── */
.topbar {
  position: relative; z-index: 2;
  display: flex; align-items: center; justify-content: space-between;
  height: 60px;
  box-sizing: border-box;
  padding: 0 28px;
  border-bottom: 0.5px solid var(--topbar-border);
  flex-shrink: 0;
}
.tb-title { font-size: 12px; color: var(--dim); font-weight: 400; }
.tb-right { display: flex; gap: 6px; }
.hamburger-btn {
  display: none;
  align-items: center; justify-content: center;
  width: 30px; height: 30px;
  border-radius: 7px;
  border: 0.5px solid var(--border);
  background: transparent;
  color: var(--text);
  cursor: pointer;
  flex-shrink: 0;
  margin-right: 10px;
}
.tb-btn {
  font-size: 12px; padding: 5px 12px;
  border-radius: 7px;
  border: 0.5px solid var(--border);
  background: transparent;
  color: var(--subtext); cursor: pointer;
  display: flex; align-items: center; gap: 5px;
  font-family: 'Inter', sans-serif;
  transition: color .15s, border-color .15s, background .15s;
}
.tb-btn:hover { color: var(--text); }
.tb-btn.active { color: var(--accent); border-color: rgb(from var(--accent) r g b / 0.35); background: rgb(from var(--accent) r g b / 0.08); }
.tb-btn.export { color: var(--text); border-color: var(--border); }
.tb-btn.theme-btn { padding: 5px 10px; }

/* 언어 드롭다운 */
.lang-dropdown { position: relative; flex-shrink: 0; }
.lang-trigger {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 500;
  font-family: 'Inter', sans-serif;
  padding: 6px 12px;
  border-radius: 8px;
  border: 0.5px solid var(--border);
  background: transparent;
  color: var(--subtext);
  cursor: pointer;
  transition: border-color .15s, color .15s;
  white-space: nowrap;
}
.lang-trigger:hover {
  color: var(--text);
  border-color: rgb(from var(--accent) r g b / 0.4);
}
.lang-menu {
  position: fixed;
  min-width: 110px;
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: 10px;
  padding: 4px;
  z-index: 9999;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.lang-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  font-family: 'Inter', sans-serif;
  color: var(--subtext);
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background .12s, color .12s;
}
.lang-option:hover {
  background: rgb(from var(--accent) r g b / 0.07);
  color: var(--text);
}
.lang-option.active {
  color: var(--accent);
  font-weight: 600;
}
.lang-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
}

/* ── Print / Export PDF ── */
@media print {
  @page { size: A4 portrait; margin: 0; }

  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }

  .sidebar, .topbar, .orb { display: none !important; }

  html, body, .shell, .main {
    background: #ffffff !important;
    height: auto !important;
  }
  .shell { display: block !important; overflow: visible !important; }
  .main  { overflow: visible !important; }

  /* 대시보드는 숨기고, 한 페이지짜리 요약 리포트만 출력 */
  .home-view { display: none !important; }

  .print-report {
    display: block !important;
    width: 210mm;
    height: 297mm;
    overflow: hidden;
  }
}

/* ── 모바일: 햄버거 → 드롭다운 메뉴 ── */
@media (max-width: 768px) {
  .hamburger-btn { display: flex; }

  .shell { flex-direction: column; }

  .sidebar {
    position: absolute;
    top: 60px; left: 0;
    width: 100%;
    max-height: calc(100vh - 60px);
    overflow-y: auto;
    z-index: 30;
    border-right: none;
    border-bottom: 0.5px solid var(--sidebar-border);
    box-shadow: 0 16px 32px rgba(0, 0, 0, 0.28);
    transform: translateY(-6px);
    opacity: 0;
    pointer-events: none;
    transition: transform .16s ease, opacity .16s ease;
  }
  .sidebar.mobile-open {
    transform: translateY(0);
    opacity: 1;
    pointer-events: auto;
  }

  .mobile-nav-backdrop {
    position: fixed;
    inset: 60px 0 0 0;
    background: rgba(0, 0, 0, 0.35);
    z-index: 20;
  }

  .topbar { padding: 0 16px; }
  .tb-title { display: none; }
}
</style>
