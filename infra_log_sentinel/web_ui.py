from __future__ import annotations


def render_chat_ui(service_name: str) -> str:
    return CHAT_UI_HTML.replace("__SERVICE_NAME__", service_name)


CHAT_UI_HTML = r"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Infra Log Sentinel</title>
  <style>
    :root {
      --bg: #f3f5f7;
      --nav: #111715;
      --nav-soft: #1b2420;
      --surface: #ffffff;
      --surface-soft: #f7f9fb;
      --surface-strong: #eef2f5;
      --line: #d9e0e5;
      --line-strong: #c5ced6;
      --text: #15201b;
      --muted: #63706a;
      --muted-strong: #44514b;
      --accent: #0f8b7d;
      --accent-strong: #08665c;
      --accent-soft: #e0f3ef;
      --blue: #315da8;
      --blue-soft: #e7eefb;
      --amber: #b7791f;
      --amber-soft: #fff2d2;
      --red: #bb241a;
      --red-soft: #fde7e5;
      --green: #1f7a4d;
      --green-soft: #e3f4eb;
      --purple: #6654b8;
      --purple-soft: #ece9fb;
      --code-bg: #0f1714;
      --code-head: #1c2a25;
      --code-text: #e9f8f2;
      --shadow: 0 16px 38px rgba(21, 32, 27, 0.09);
      --shadow-soft: 0 6px 18px rgba(21, 32, 27, 0.06);
      --radius: 8px;
    }

    * {
      box-sizing: border-box;
      min-width: 0;
    }

    html,
    body {
      margin: 0;
      height: 100%;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
      overflow: hidden;
    }

    button,
    textarea {
      font: inherit;
    }

    button {
      letter-spacing: 0;
    }

    .app-shell {
      display: grid;
      grid-template-columns: 292px minmax(0, 1fr) 326px;
      height: 100vh;
      width: 100%;
      max-width: 100vw;
      overflow: hidden;
    }

    .nav {
      background: var(--nav);
      color: #eff6f3;
      border-right: 1px solid #202b27;
      padding: 20px 16px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      height: 100vh;
      overflow-y: auto;
      overscroll-behavior: contain;
    }

    .brand {
      display: grid;
      grid-template-columns: 44px minmax(0, 1fr);
      gap: 12px;
      align-items: center;
      padding-bottom: 4px;
    }

    .mark {
      width: 44px;
      height: 44px;
      border-radius: var(--radius);
      display: grid;
      place-items: center;
      background: #eff6f3;
      color: #0e1714;
      font-size: 15px;
      font-weight: 900;
      letter-spacing: 0;
    }

    .brand h1 {
      margin: 0;
      font-size: 17px;
      line-height: 1.15;
      font-weight: 850;
    }

    .brand p {
      margin: 4px 0 0;
      color: #9eb0a8;
      font-size: 12px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .nav-panel {
      border: 1px solid #26332e;
      border-radius: var(--radius);
      background: var(--nav-soft);
      padding: 12px;
    }

    .nav-title {
      margin: 0 0 10px;
      color: #9eb0a8;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .runtime-state {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .state-copy strong {
      display: block;
      font-size: 15px;
    }

    .state-copy span {
      display: block;
      margin-top: 2px;
      color: #9eb0a8;
      font-size: 12px;
    }

    .state-pill,
    .chip,
    .mini-chip {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-height: 28px;
      border-radius: 999px;
      white-space: nowrap;
    }

    .state-pill {
      padding: 3px 9px;
      background: #20352e;
      color: #d8efe7;
      font-size: 12px;
      font-weight: 800;
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--amber);
    }

    .dot.ok {
      background: #35c07e;
    }

    .dot.bad {
      background: #ff5a4f;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .metric {
      min-height: 72px;
      border-radius: var(--radius);
      background: #19221f;
      border: 1px solid #26332e;
      padding: 10px;
    }

    .metric span {
      display: block;
      color: #98aaa2;
      font-size: 11px;
      margin-bottom: 8px;
    }

    .metric strong {
      display: block;
      color: #f7fbf9;
      font-size: 25px;
      line-height: 1;
    }

    .metric.critical strong {
      color: #ff7c72;
    }

    .metric.warning strong {
      color: #ffd36d;
    }

    .quick-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      width: 100%;
      max-width: 100%;
    }

    .quick {
      width: 100%;
      min-width: 0;
      min-height: 40px;
      border: 1px solid #2c3934;
      border-radius: var(--radius);
      background: #151d1a;
      color: #e8f0ed;
      display: grid;
      grid-template-columns: 24px minmax(0, 1fr);
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      text-align: left;
      cursor: pointer;
    }

    .quick:hover {
      border-color: #4cb8a9;
      background: #1c2a25;
    }

    .quick .icon {
      width: 24px;
      height: 24px;
      display: grid;
      place-items: center;
      border-radius: 6px;
      background: #23332e;
      color: #9de4d9;
      font-weight: 850;
      font-size: 12px;
    }

    .quick span:last-child {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .nav-foot {
      margin-top: auto;
      color: #9eb0a8;
      font-size: 12px;
      line-height: 1.45;
    }

    .workspace {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
      min-width: 0;
      height: 100vh;
      background: var(--bg);
      overflow: hidden;
    }

    .workspace-header {
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(16px);
      padding: 16px 22px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      z-index: 5;
    }

    .title-block {
      min-width: 0;
    }

    .eyebrow {
      margin: 0 0 4px;
      color: var(--accent-strong);
      font-size: 11px;
      font-weight: 850;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .workspace-header h2 {
      margin: 0;
      font-size: 22px;
      line-height: 1.15;
      letter-spacing: 0;
    }

    .workspace-header small {
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 13px;
    }

    .header-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
    }

    .chip {
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--muted-strong);
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 750;
      box-shadow: var(--shadow-soft);
      max-width: 100%;
    }

    .chip strong {
      color: var(--text);
    }

    .conversation {
      min-height: 0;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 24px 22px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      overscroll-behavior: contain;
    }

    .conversation-inner {
      width: min(100%, 920px);
      max-width: 100%;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .message {
      display: grid;
      grid-template-columns: 38px minmax(0, 1fr);
      gap: 12px;
      align-items: start;
    }

    .message.user {
      grid-template-columns: minmax(0, 1fr) 38px;
      margin-left: min(22%, 220px);
    }

    .avatar {
      width: 38px;
      height: 38px;
      border-radius: var(--radius);
      display: grid;
      place-items: center;
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--accent-strong);
      font-size: 12px;
      font-weight: 900;
    }

    .message.user .avatar {
      grid-column: 2;
      background: #18231f;
      color: #ffffff;
      border-color: #18231f;
    }

    .bubble {
      min-width: 0;
      max-width: 100%;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      box-shadow: var(--shadow-soft);
      overflow-wrap: anywhere;
    }

    .message.user .bubble {
      grid-column: 1;
      grid-row: 1;
      background: #18231f;
      color: #ffffff;
      border-color: #18231f;
      padding: 13px 15px;
      line-height: 1.5;
      white-space: pre-wrap;
    }

    .message.agent.typing .bubble {
      padding: 14px 16px;
      color: var(--muted);
    }

    .answer {
      padding: 17px 18px;
      line-height: 1.58;
      overflow-wrap: anywhere;
      word-break: normal;
    }

    .answer > :first-child {
      margin-top: 0;
    }

    .answer > :last-child {
      margin-bottom: 0;
    }

    .answer h2,
    .answer h3,
    .answer h4 {
      margin: 18px 0 9px;
      line-height: 1.25;
      letter-spacing: 0;
    }

    .answer h2 {
      font-size: 18px;
      color: var(--accent-strong);
      padding-bottom: 8px;
      border-bottom: 1px solid var(--line);
    }

    .answer h3 {
      font-size: 16px;
      color: var(--muted-strong);
    }

    .answer h4 {
      font-size: 14px;
      color: var(--blue);
    }

    .answer p {
      margin: 9px 0;
      overflow-wrap: anywhere;
    }

    .answer a {
      color: var(--blue);
      font-weight: 800;
    }

    .answer ul,
    .answer ol {
      margin: 8px 0 13px 22px;
      padding: 0;
    }

    .answer li {
      margin: 5px 0;
    }

    .answer strong {
      color: #0f1c18;
      font-weight: 850;
    }

    .inline-code {
      display: inline-block;
      max-width: 100%;
      padding: 1px 6px;
      border: 1px solid #c8d6d1;
      border-radius: 6px;
      background: #f2f7f5;
      color: #075f56;
      font-family: "Cascadia Mono", "Fira Code", Consolas, monospace;
      font-size: 0.92em;
      vertical-align: baseline;
    }

    .severity {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 850;
      letter-spacing: 0.02em;
    }

    .severity.critical {
      background: var(--red-soft);
      color: var(--red);
    }

    .severity.error {
      background: #fce7d5;
      color: #a94f0b;
    }

    .severity.warning {
      background: var(--amber-soft);
      color: var(--amber);
    }

    .severity.info {
      background: var(--blue-soft);
      color: var(--blue);
    }

    .code-block {
      margin: 13px 0;
      overflow: hidden;
      border: 1px solid #20312b;
      border-radius: var(--radius);
      background: var(--code-bg);
    }

    .code-head {
      min-height: 40px;
      padding: 7px 9px 7px 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      background: var(--code-head);
      color: #c9ded6;
      font-size: 12px;
      font-weight: 800;
      border-bottom: 1px solid #273a33;
    }

    .copy-button,
    .command-copy {
      min-height: 30px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 850;
    }

    .copy-button {
      border: 1px solid rgba(255, 255, 255, 0.18);
      background: rgba(255, 255, 255, 0.08);
      color: #ffffff;
      padding: 0 10px;
    }

    .copy-button:hover {
      background: rgba(255, 255, 255, 0.16);
    }

    .code-block pre {
      margin: 0;
      padding: 15px;
      overflow-x: auto;
    }

    .code-block code {
      color: var(--code-text);
      font-family: "Cascadia Mono", "Fira Code", Consolas, monospace;
      font-size: 13px;
      line-height: 1.55;
      white-space: pre;
    }

    .command-card {
      margin: 11px 0;
      border: 1px solid #bfd9d2;
      border-left: 4px solid var(--accent);
      border-radius: var(--radius);
      background: #f8fcfa;
      overflow: hidden;
    }

    .command-head {
      min-height: 40px;
      padding: 8px 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      background: var(--accent-soft);
      border-bottom: 1px solid #d2e7e1;
    }

    .phase {
      color: var(--accent-strong);
      font-size: 12px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .command-copy {
      border: 1px solid #91bdb4;
      background: #ffffff;
      color: var(--accent-strong);
      padding: 0 10px;
    }

    .command-copy:hover {
      background: #eef8f5;
    }

    .command-text {
      display: block;
      padding: 12px 13px;
      color: #10251e;
      font-family: "Cascadia Mono", "Fira Code", Consolas, monospace;
      font-size: 13px;
      line-height: 1.5;
      white-space: pre-wrap;
    }

    .why {
      margin: -4px 0 9px 0;
      padding-left: 13px;
      color: var(--muted);
      font-size: 13px;
      border-left: 2px solid var(--line);
    }

    .answer table {
      width: 100%;
      border-collapse: collapse;
      margin: 13px 0;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      font-size: 13px;
    }

    .answer th,
    .answer td {
      padding: 9px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }

    .answer th {
      background: #eef4f2;
      color: var(--accent-strong);
      font-weight: 850;
    }

    .answer tr:last-child td {
      border-bottom: 0;
    }

    .answer hr {
      border: 0;
      border-top: 1px solid var(--line);
      margin: 15px 0;
    }

    .composer {
      border-top: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.9);
      padding: 14px 22px 18px;
      position: sticky;
      bottom: 0;
      z-index: 8;
    }

    .composer-shell {
      width: min(100%, 920px);
      margin: 0 auto;
      border: 1px solid var(--line-strong);
      border-radius: var(--radius);
      background: var(--surface);
      overflow: hidden;
      box-shadow: var(--shadow);
    }

    textarea {
      width: 100%;
      min-height: 78px;
      max-height: 180px;
      display: block;
      border: 0;
      outline: none;
      resize: vertical;
      padding: 15px 16px;
      color: var(--text);
      background: transparent;
    }

    .composer-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border-top: 1px solid var(--line);
      padding: 10px;
    }

    .toggle {
      display: inline-flex;
      align-items: center;
      gap: 9px;
      color: var(--muted);
      font-size: 13px;
      user-select: none;
    }

    .toggle input {
      accent-color: var(--accent);
    }

    .send {
      min-width: 96px;
      min-height: 40px;
      border: 0;
      border-radius: var(--radius);
      background: var(--accent);
      color: #ffffff;
      cursor: pointer;
      font-weight: 850;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .send:hover {
      background: var(--accent-strong);
    }

    .send:disabled {
      cursor: wait;
      opacity: 0.68;
    }

    .insight-rail {
      border-left: 1px solid var(--line);
      background: #fbfcfd;
      padding: 14px;
      display: grid;
      grid-template-rows: minmax(0, 1fr) auto auto auto;
      gap: 10px;
      min-width: 0;
      height: 100vh;
      overflow: hidden;
      overscroll-behavior: contain;
    }

    .rail-section {
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      padding: 11px;
      box-shadow: var(--shadow-soft);
      min-height: 0;
    }

    .rail-section h3 {
      margin: 0 0 9px;
      font-size: 14px;
      letter-spacing: 0;
    }

    .rail-section:first-child {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .alert-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      min-height: 0;
      overflow-y: auto;
      padding-right: 3px;
      overscroll-behavior: contain;
    }

    .alert-item {
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 8px;
      background: var(--surface-soft);
    }

    .alert-item strong {
      display: block;
      margin: 5px 0 3px;
      font-size: 12px;
      line-height: 1.25;
    }

    .alert-item p {
      margin: 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
    }

    .mini-chip {
      min-height: 22px;
      padding: 2px 7px;
      background: var(--surface-strong);
      color: var(--muted-strong);
      font-size: 11px;
      font-weight: 850;
    }

    .mini-chip.critical {
      background: var(--red-soft);
      color: var(--red);
    }

    .mini-chip.error {
      background: #fce7d5;
      color: #9a4f10;
    }

    .mini-chip.warning {
      background: var(--amber-soft);
      color: var(--amber);
    }

    .control-list,
    .facts {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .control-item,
    .fact {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      min-height: 28px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 6px;
      color: var(--muted);
      font-size: 12px;
    }

    .control-item:last-child,
    .fact:last-child {
      border-bottom: 0;
      padding-bottom: 0;
    }

    .control-item strong,
    .fact strong {
      color: var(--text);
      font-size: 13px;
      text-align: right;
      overflow-wrap: anywhere;
    }

    .control-badge {
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 850;
      color: var(--green);
      background: var(--green-soft);
    }

    .control-badge.paused {
      color: var(--amber);
      background: var(--amber-soft);
    }

    .domain-bars {
      display: flex;
      flex-direction: column;
      gap: 7px;
    }

    .domain-row {
      display: grid;
      grid-template-columns: 74px minmax(0, 1fr) 28px;
      gap: 8px;
      align-items: center;
      color: var(--muted);
      font-size: 12px;
    }

    .bar {
      height: 8px;
      border-radius: 999px;
      overflow: hidden;
      background: var(--surface-strong);
    }

    .bar span {
      display: block;
      height: 100%;
      width: 0;
      background: var(--accent);
    }

    .empty {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }

    @media (max-width: 1180px) {
      .app-shell {
        grid-template-columns: 280px minmax(0, 1fr);
      }

      .insight-rail {
        grid-column: 1 / -1;
        border-left: 0;
        border-top: 1px solid var(--line);
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
    }

    @media (max-width: 860px) {
      .app-shell {
        grid-template-columns: 1fr;
        max-width: 100vw;
        overflow-x: hidden;
      }

      .nav {
        border-right: 0;
      }

      .quick-list {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .workspace-header {
        align-items: flex-start;
        flex-direction: column;
      }

      .header-actions {
        justify-content: flex-start;
      }

      .insight-rail {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 620px) {
      .app-shell,
      .nav,
      .workspace,
      .insight-rail,
      .workspace-header,
      .conversation,
      .composer {
        width: 100vw;
        max-width: 100vw;
        overflow-x: hidden;
      }

      .workspace {
        padding-right: 18px;
      }

      .workspace-header,
      .conversation,
      .composer {
        width: 100%;
        max-width: 100%;
      }

      .nav {
        gap: 12px;
        padding: 14px;
      }

      .runtime-state {
        align-items: flex-start;
        flex-direction: column;
      }

      .signal-panel,
      .nav-foot {
        display: none;
      }

      .quick-list {
        grid-template-columns: 1fr;
        overflow: hidden;
      }

      .quick-panel {
        overflow: hidden;
      }

      .quick {
        min-height: 36px;
        font-size: 14px;
      }

      .quick .icon {
        width: 22px;
        height: 22px;
      }

      .workspace-header {
        padding: 14px;
        max-width: 100vw;
        overflow-x: hidden;
      }

      .workspace-header h2 {
        font-size: 20px;
      }

      .workspace-header small,
      .title-block {
        max-width: 100%;
        overflow-wrap: anywhere;
      }

      .header-actions {
        width: 100%;
        max-width: calc(100vw - 28px);
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-start;
        padding-right: 8px;
      }

      .header-actions .chip {
        flex: 0 1 auto;
        min-width: 0;
        justify-content: center;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .header-actions .chip strong {
        display: inline-block;
        max-width: 112px;
        overflow: hidden;
        text-overflow: ellipsis;
        vertical-align: bottom;
      }

      .header-actions .chip:last-child {
        grid-column: auto;
      }

      .conversation {
        padding: 18px 12px;
        max-width: 100vw;
        overflow-x: hidden;
      }

      .conversation-inner,
      .composer-shell,
      .bubble,
      .answer {
        width: 100%;
        max-width: 100%;
      }

      .answer {
        padding: 16px;
      }

      .message,
      .message.user {
        grid-template-columns: 1fr;
        margin-left: 0;
        width: calc(100vw - 56px) !important;
        max-width: calc(100vw - 56px) !important;
        overflow: hidden;
      }

      .avatar {
        display: none;
      }

      .message.user .bubble {
        grid-column: 1;
      }

      .message.agent .bubble,
      .message.user .bubble {
        width: 100% !important;
        max-width: 100% !important;
      }

      .composer {
        padding: 12px;
      }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="nav">
      <div class="brand">
        <div class="mark">ILS</div>
        <div>
          <h1>Infra Log Sentinel</h1>
          <p>__SERVICE_NAME__</p>
        </div>
      </div>

      <section class="nav-panel runtime-panel">
        <p class="nav-title">Runtime posture</p>
        <div class="runtime-state">
          <div class="state-copy">
            <strong id="posture-label">Checking</strong>
            <span id="posture-detail">Waiting for telemetry</span>
          </div>
          <span class="state-pill"><span id="health-dot" class="dot"></span><span id="health-text">syncing</span></span>
        </div>
      </section>

      <section class="nav-panel signal-panel">
        <p class="nav-title">Last 24h signal</p>
        <div class="metric-grid">
          <div class="metric">
            <span>Events</span>
            <strong id="metric-events">-</strong>
          </div>
          <div class="metric critical">
            <span>Critical</span>
            <strong id="metric-critical">-</strong>
          </div>
          <div class="metric">
            <span>Error</span>
            <strong id="metric-error">-</strong>
          </div>
          <div class="metric warning">
            <span>Warning</span>
            <strong id="metric-warning">-</strong>
          </div>
        </div>
      </section>

      <section class="nav-panel quick-panel">
        <p class="nav-title">Quick actions</p>
        <div class="quick-list">
          <button class="quick" type="button" data-prompt="tóm tắt log hôm nay"><span class="icon">S</span><span>Tóm tắt hôm nay</span></button>
          <button class="quick" type="button" data-prompt="alert nào cần ưu tiên và vì sao"><span class="icon">P</span><span>Ưu tiên alert</span></button>
          <button class="quick" type="button" data-prompt="phân tích lỗi nghiêm trọng và đưa command xử lý"><span class="icon">C</span><span>Command xử lý</span></button>
          <button class="quick" type="button" data-prompt="trạng thái control"><span class="icon">R</span><span>Runtime control</span></button>
          <button class="quick" type="button" data-prompt="tạm ngừng sinh log trong 5 phút"><span class="icon">G</span><span>Tạm ngừng sinh log</span></button>
          <button class="quick" type="button" data-prompt="gửi báo cáo hôm nay qua Gmail"><span class="icon">M</span><span>Gửi report Gmail</span></button>
        </div>
      </section>

      <div class="nav-foot">
        Agent hỏi lại khi thiếu target, value, thời gian hoặc kênh gửi. Các thao tác thật chỉ chạy khi tắt Preview only.
      </div>
    </aside>

    <main class="workspace">
      <header class="workspace-header">
        <div class="title-block">
          <p class="eyebrow">AI operations copilot</p>
          <h2>Infrastructure Log Intelligence</h2>
          <small>Phân tích Network, Linux, Windows, VMware log với runbook command và runtime controls.</small>
        </div>
        <div class="header-actions">
          <span class="chip">Model <strong id="model-chip">MiniMax M2.5</strong></span>
          <span class="chip">Window <strong id="window-chip">24h</strong></span>
          <span class="chip">Mode <strong id="mode-chip">runtime</strong></span>
        </div>
      </header>

      <section class="conversation" aria-live="polite">
        <div id="conversation" class="conversation-inner"></div>
      </section>

      <footer class="composer">
        <form id="chat-form" class="composer-shell">
          <textarea id="prompt" rows="2" placeholder="Hỏi agent về log, alert, report, command xử lý hoặc runtime control..."></textarea>
          <div class="composer-actions">
            <label class="toggle">
              <input id="dry-run" type="checkbox" checked>
              Preview only
            </label>
            <button id="send" class="send" type="submit"><span>Send</span><span>›</span></button>
          </div>
        </form>
      </footer>
    </main>

    <aside class="insight-rail">
      <section class="rail-section">
        <h3>Priority queue</h3>
        <div id="alert-list" class="alert-list">
          <p class="empty">No alert context loaded yet.</p>
        </div>
      </section>

      <section class="rail-section">
        <h3>Runtime controls</h3>
        <div class="control-list">
          <div class="control-item"><span>Telegram alerts</span><strong id="control-telegram">-</strong></div>
          <div class="control-item"><span>Gmail reports</span><strong id="control-email">-</strong></div>
          <div class="control-item"><span>Log generator</span><strong id="control-loggen">-</strong></div>
          <div class="control-item"><span>Generator interval</span><strong id="control-interval">-</strong></div>
        </div>
      </section>

      <section class="rail-section">
        <h3>Environment</h3>
        <div class="facts">
          <div class="fact"><span>Report time</span><strong id="fact-report-time">-</strong></div>
          <div class="fact"><span>Scan interval</span><strong id="fact-scan">-</strong></div>
          <div class="fact"><span>Timezone</span><strong id="fact-timezone">-</strong></div>
          <div class="fact"><span>Source mode</span><strong id="fact-source">-</strong></div>
        </div>
      </section>

      <section class="rail-section">
        <h3>Domain mix</h3>
        <div id="domain-bars" class="domain-bars">
          <p class="empty">Waiting for status.</p>
        </div>
      </section>
    </aside>
  </div>

  <script>
    const conversation = document.getElementById("conversation");
    const form = document.getElementById("chat-form");
    const promptBox = document.getElementById("prompt");
    const dryRunBox = document.getElementById("dry-run");
    const sendButton = document.getElementById("send");

    const state = {
      busy: false
    };

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function linkify(value) {
      const escaped = escapeHtml(value);
      return escaped.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noreferrer">$1</a>');
    }

    function inlineFormat(value) {
      let html = escapeHtml(value);
      html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
      html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/\[(CRITICAL|ERROR|WARNING|INFO)\]/gi, function(_, level) {
        return '<span class="severity ' + level.toLowerCase() + '">' + level.toUpperCase() + '</span>';
      });
      html = html.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noreferrer">$1</a>');
      return html;
    }

    function renderAgentContent(text) {
      const normalized = String(text || "").replace(/\r\n/g, "\n");
      const parts = [];
      const fenceRegex = /```([A-Za-z0-9_-]*)\n([\s\S]*?)```/g;
      let lastIndex = 0;
      let match;

      while ((match = fenceRegex.exec(normalized)) !== null) {
        if (match.index > lastIndex) {
          parts.push(renderMarkdownBlock(normalized.slice(lastIndex, match.index)));
        }
        parts.push(renderCodeBlock(match[2], match[1] || "command"));
        lastIndex = fenceRegex.lastIndex;
      }

      if (lastIndex < normalized.length) {
        parts.push(renderMarkdownBlock(normalized.slice(lastIndex)));
      }

      return '<div class="answer">' + parts.join("") + '</div>';
    }

    function renderMarkdownBlock(text) {
      const lines = text.split("\n");
      const html = [];
      let listType = null;
      let listItems = [];
      let tableRows = [];

      function flushList() {
        if (!listType) {
          return;
        }
        html.push('<' + listType + '>' + listItems.map(function(item) {
          return '<li>' + inlineFormat(item) + '</li>';
        }).join("") + '</' + listType + '>');
        listType = null;
        listItems = [];
      }

      function flushTable() {
        if (!tableRows.length) {
          return;
        }
        const rows = tableRows.map(parseTableRow);
        const header = rows.shift() || [];
        if (rows.length && rows[0].every(function(cell) { return /^-+$/.test(cell.replace(/:/g, "").trim()); })) {
          rows.shift();
        }
        if (!header.length) {
          tableRows = [];
          return;
        }
        html.push(
          '<table><thead><tr>' +
          header.map(function(cell) { return '<th>' + inlineFormat(cell) + '</th>'; }).join("") +
          '</tr></thead><tbody>' +
          rows.map(function(row) {
            return '<tr>' + row.map(function(cell) { return '<td>' + inlineFormat(cell) + '</td>'; }).join("") + '</tr>';
          }).join("") +
          '</tbody></table>'
        );
        tableRows = [];
      }

      for (let i = 0; i < lines.length; i++) {
        const rawLine = lines[i];
        const line = rawLine.trim();

        if (!line) {
          flushList();
          flushTable();
          continue;
        }

        if (isTableLine(line)) {
          flushList();
          tableRows.push(line);
          continue;
        }
        flushTable();

        const commandMatch = rawLine.match(/^\s*-\s*(Verify|Investigate|Remediate|Validate|Check|Analyze|Fix):\s*(.+)$/i);
        if (commandMatch) {
          flushList();
          html.push(renderCommandCard(commandMatch[1], commandMatch[2]));
          continue;
        }

        const whyMatch = rawLine.match(/^\s*Why:\s*(.+)$/i);
        if (whyMatch) {
          flushList();
          html.push('<p class="why">' + inlineFormat(whyMatch[1]) + '</p>');
          continue;
        }

        const heading = line.match(/^(#{1,4})\s+(.+)$/);
        if (heading) {
          flushList();
          const level = Math.min(heading[1].length + 1, 4);
          html.push('<h' + level + '>' + inlineFormat(heading[2]) + '</h' + level + '>');
          continue;
        }

        if (/^-{3,}$/.test(line)) {
          flushList();
          html.push("<hr>");
          continue;
        }

        const bullet = line.match(/^[-*]\s+(.+)$/);
        if (bullet) {
          if (listType !== "ul") {
            flushList();
            listType = "ul";
          }
          listItems.push(bullet[1]);
          continue;
        }

        const numbered = line.match(/^\d+\.\s+(.+)$/);
        if (numbered) {
          if (listType !== "ol") {
            flushList();
            listType = "ol";
          }
          listItems.push(numbered[1]);
          continue;
        }

        flushList();
        html.push('<p>' + inlineFormat(line) + '</p>');
      }

      flushList();
      flushTable();
      return html.join("");
    }

    function isTableLine(line) {
      return line.includes("|") && line.split("|").length >= 3;
    }

    function parseTableRow(line) {
      return line.replace(/^\|/, "").replace(/\|$/, "").split("|").map(function(cell) {
        return cell.trim();
      });
    }

    function renderCodeBlock(code, lang) {
      return '' +
        '<div class="code-block">' +
          '<div class="code-head"><span>' + escapeHtml(lang || "command") + '</span><button class="copy-button" type="button" data-copy="code">Copy</button></div>' +
          '<pre><code>' + escapeHtml(String(code || "").trim()) + '</code></pre>' +
        '</div>';
    }

    function renderCommandCard(phase, command) {
      return '' +
        '<div class="command-card">' +
          '<div class="command-head"><span class="phase">' + escapeHtml(phase) + '</span><button class="command-copy" type="button" data-copy="command">Copy</button></div>' +
          '<code class="command-text">' + escapeHtml(String(command || "").trim()) + '</code>' +
        '</div>';
    }

    function appendMessage(role, text, extraClass) {
      const row = document.createElement("div");
      row.className = "message " + role + (extraClass ? " " + extraClass : "");

      const avatar = document.createElement("div");
      avatar.className = "avatar";
      avatar.textContent = role === "user" ? "ME" : "AI";

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.innerHTML = role === "agent" ? renderAgentContent(text) : linkify(text);

      if (role === "user") {
        row.appendChild(bubble);
        row.appendChild(avatar);
      } else {
        row.appendChild(avatar);
        row.appendChild(bubble);
      }

      conversation.appendChild(row);
      conversation.parentElement.scrollTop = conversation.parentElement.scrollHeight;
      return row;
    }

    async function copyText(value, button) {
      try {
        await navigator.clipboard.writeText(value);
      } catch (error) {
        const textarea = document.createElement("textarea");
        textarea.value = value;
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      }
      const original = button.textContent;
      button.textContent = "Copied";
      setTimeout(function() {
        button.textContent = original;
      }, 1400);
    }

    function setBusy(value) {
      state.busy = value;
      sendButton.disabled = value;
      sendButton.querySelector("span:first-child").textContent = value ? "Working" : "Send";
    }

    async function askAgent(message) {
      const text = message.trim();
      if (!text || state.busy) {
        return;
      }

      appendMessage("user", text);
      promptBox.value = "";
      setBusy(true);
      const typingRow = appendMessage("agent", "Đang phân tích ngữ cảnh, log và runbook...", "typing");

      try {
        const response = await fetch("/invocations", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            message: text,
            dry_run: dryRunBox.checked
          })
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.message || payload.error || "Request failed");
        }
        typingRow.remove();
        appendMessage("agent", payload.answer || "No answer returned.");
        refreshStatus();
      } catch (error) {
        typingRow.remove();
        appendMessage("agent", "Không xử lý được request: " + error.message);
      } finally {
        setBusy(false);
        promptBox.focus();
      }
    }

    function setText(id, value) {
      const el = document.getElementById(id);
      if (el) {
        el.textContent = value;
      }
    }

    function formatControl(control) {
      if (!control) {
        return '<span class="control-badge">running</span>';
      }
      if (control.paused) {
        return '<span class="control-badge paused">paused</span>';
      }
      return '<span class="control-badge">running</span>';
    }

    function severityClass(severity) {
      const value = String(severity || "info").toLowerCase();
      if (["critical", "error", "warning"].includes(value)) {
        return value;
      }
      return "info";
    }

    function updatePosture(severity) {
      const critical = severity.critical || 0;
      const error = severity.error || 0;
      const warning = severity.warning || 0;
      if (critical > 0) {
        setText("posture-label", "Incident");
        setText("posture-detail", critical + " critical alert cần xử lý trước");
        return;
      }
      if (error > 0 || warning > 0) {
        setText("posture-label", "Watch");
        setText("posture-detail", (error + warning) + " alert cần theo dõi");
        return;
      }
      setText("posture-label", "Stable");
      setText("posture-detail", "Không có alert mức cao trong cửa sổ báo cáo");
    }

    function renderAlerts(alerts) {
      const list = document.getElementById("alert-list");
      if (!alerts || !alerts.length) {
        list.innerHTML = '<p class="empty">Không có warning/error/critical trong cửa sổ hiện tại.</p>';
        return;
      }
      list.innerHTML = alerts.slice(0, 5).map(function(alert) {
        const severity = severityClass(alert.severity);
        return '' +
          '<article class="alert-item">' +
            '<span class="mini-chip ' + severity + '">' + escapeHtml(String(alert.severity || "info").toUpperCase()) + '</span>' +
            '<strong>' + escapeHtml(alert.domain || "-") + " / " + escapeHtml(alert.source || "-") + '</strong>' +
            '<p>' + escapeHtml(alert.event_type || "-") + ': ' + escapeHtml(alert.message || "") + '</p>' +
          '</article>';
      }).join("");
    }

    function renderDomainBars(domainCounts) {
      const root = document.getElementById("domain-bars");
      const entries = Object.entries(domainCounts || {});
      if (!entries.length) {
        root.innerHTML = '<p class="empty">Chưa có domain count.</p>';
        return;
      }
      const max = Math.max(...entries.map(function(item) { return Number(item[1]) || 0; }), 1);
      root.innerHTML = entries.map(function(item) {
        const name = item[0];
        const value = Number(item[1]) || 0;
        const width = Math.round((value / max) * 100);
        return '' +
          '<div class="domain-row">' +
            '<span>' + escapeHtml(name) + '</span>' +
            '<div class="bar"><span style="width:' + width + '%"></span></div>' +
            '<strong>' + value + '</strong>' +
          '</div>';
      }).join("");
    }

    async function refreshStatus() {
      try {
        const response = await fetch("/status");
        const status = await response.json();
        if (!response.ok) {
          throw new Error(status.message || "status failed");
        }

        document.getElementById("health-dot").className = "dot ok";
        setText("health-text", "online");

        const config = status.config || {};
        const severity = status.severity_counts || {};
        setText("metric-events", String(status.report_window_events ?? status.parsed_events ?? "-"));
        setText("metric-critical", String(severity.critical || 0));
        setText("metric-error", String(severity.error || 0));
        setText("metric-warning", String(severity.warning || 0));
        updatePosture(severity);

        const modelName = config.llm_model ? String(config.llm_model).split("/").pop() : "MiniMax M2.5";
        setText("model-chip", modelName);
        setText("window-chip", String(config.report_lookback_hours || 24) + "h");
        setText("mode-chip", config.log_source_mode || "runtime");
        setText("fact-report-time", config.report_time || "-");
        setText("fact-scan", String(config.scan_interval_seconds || "-") + "s");
        setText("fact-timezone", config.app_timezone || "-");
        setText("fact-source", config.log_source_mode || "-");

        const pauses = (status.runtime_controls && status.runtime_controls.pauses) || {};
        document.getElementById("control-telegram").innerHTML = formatControl(pauses.telegram_alerts);
        document.getElementById("control-email").innerHTML = formatControl(pauses.email_reports);
        document.getElementById("control-loggen").innerHTML = formatControl(pauses.log_generation);

        const values = (status.runtime_controls && status.runtime_controls.values) || {};
        const interval = values.demo_log_interval_seconds || config.demo_log_interval_seconds || "-";
        setText("control-interval", String(interval) + "s");

        renderAlerts(status.top_alerts || []);
        renderDomainBars(status.domain_counts || {});
      } catch (error) {
        document.getElementById("health-dot").className = "dot bad";
        setText("health-text", "offline");
        setText("posture-label", "Degraded");
        setText("posture-detail", "Không đọc được endpoint status");
      }
    }

    form.addEventListener("submit", function(event) {
      event.preventDefault();
      askAgent(promptBox.value);
    });

    promptBox.addEventListener("keydown", function(event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

    document.querySelectorAll("[data-prompt]").forEach(function(button) {
      button.addEventListener("click", function() {
        askAgent(button.dataset.prompt);
      });
    });

    conversation.addEventListener("click", function(event) {
      const button = event.target.closest("[data-copy]");
      if (!button) {
        return;
      }
      const codeBlock = button.closest(".code-block");
      const commandCard = button.closest(".command-card");
      if (codeBlock) {
        const code = codeBlock.querySelector("code");
        copyText(code ? code.textContent : "", button);
        return;
      }
      if (commandCard) {
        const command = commandCard.querySelector(".command-text");
        copyText(command ? command.textContent : "", button);
      }
    });

    appendMessage(
      "agent",
      "**Xin chào.** Mình đang vận hành ở chế độ AI operations copilot. Anh có thể hỏi về log, yêu cầu command kiểm tra, tạo report, gửi Gmail, hoặc điều khiển alert/log generator. Nếu câu lệnh có thể thay đổi runtime nhưng thiếu ngữ cảnh, mình sẽ hỏi lại trước."
    );
    refreshStatus();
    setInterval(refreshStatus, 15000);
  </script>
</body>
</html>
"""
