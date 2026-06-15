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
    textarea,
    input,
    select {
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

    .rca-workspace {
      width: min(100%, 920px);
      max-width: 100%;
      margin: 0 auto 18px;
      border: 1px solid #b9d9d1;
      border-left: 4px solid var(--accent);
      border-radius: var(--radius);
      background: #ffffff;
      box-shadow: var(--shadow-soft);
      overflow: hidden;
    }

    .rca-workspace-head {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 14px;
      align-items: start;
      padding: 13px 15px;
      background: linear-gradient(90deg, #eefaf6 0%, #f8fbff 100%);
      border-bottom: 1px solid #d1e6df;
    }

    .rca-workspace-kicker {
      margin: 0 0 4px;
      color: var(--accent-strong);
      font-size: 11px;
      font-weight: 950;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .rca-workspace-title {
      margin: 0;
      font-size: 17px;
      line-height: 1.25;
      font-weight: 950;
    }

    .rca-confidence-pill {
      min-width: 72px;
      padding: 7px 10px;
      border: 1px solid #b8d8d1;
      border-radius: var(--radius);
      background: #ffffff;
      color: var(--accent-strong);
      text-align: center;
      font-size: 20px;
      font-weight: 950;
      line-height: 1;
    }

    .rca-confidence-pill span {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 10px;
      font-weight: 850;
      text-transform: uppercase;
    }

    .rca-workspace-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.7fr) minmax(160px, 0.55fr);
      gap: 10px;
      padding: 12px;
      border-bottom: 1px solid var(--line);
    }

    .rca-field {
      display: grid;
      gap: 6px;
      color: var(--muted-strong);
      font-size: 11px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .rca-field-hint {
      margin: -2px 0 0;
      color: var(--muted);
      font-size: 11px;
      font-weight: 650;
      line-height: 1.35;
      letter-spacing: 0;
      text-transform: none;
    }

    .rca-field textarea,
    .rca-field input,
    .rca-field select {
      width: 100%;
      border: 1px solid var(--line-strong);
      border-radius: var(--radius);
      background: #fbfcfd;
      color: var(--text);
      padding: 9px 10px;
      font-size: 13px;
      font-weight: 650;
      text-transform: none;
      letter-spacing: 0;
      outline: none;
    }

    .rca-field textarea {
      min-height: 76px;
      resize: vertical;
    }

    .rca-field input:focus,
    .rca-field select:focus,
    .rca-field textarea:focus {
      border-color: #64bbae;
      box-shadow: 0 0 0 3px rgba(15, 139, 125, 0.12);
    }

    .rca-field-stack {
      display: grid;
      gap: 10px;
    }

    .rca-workspace-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      padding: 0 12px 12px;
    }

    .rca-workspace-button {
      min-height: 36px;
      border: 1px solid #94c9be;
      border-radius: var(--radius);
      background: var(--accent);
      color: #ffffff;
      padding: 0 12px;
      font-size: 12px;
      font-weight: 950;
      cursor: pointer;
    }

    .rca-workspace-button.secondary {
      background: #ffffff;
      color: var(--accent-strong);
    }

    .rca-workspace-button.danger {
      background: #fff7ed;
      border-color: #fed7aa;
      color: #9a3412;
    }

    .rca-workspace-button:hover {
      filter: brightness(0.97);
    }

    .rca-workspace-button:disabled {
      cursor: wait;
      opacity: 0.6;
    }

    .rca-workspace-result {
      display: grid;
      grid-template-columns: minmax(0, 1.08fr) minmax(0, 0.92fr);
      gap: 10px;
      padding: 0 12px 12px;
    }

    .rca-result-block {
      min-height: 92px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface-soft);
      padding: 10px;
    }

    .rca-result-block h4 {
      margin: 0 0 7px;
      color: var(--accent-strong);
      font-size: 11px;
      font-weight: 950;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .rca-root-cause {
      margin: 0;
      font-size: 14px;
      line-height: 1.45;
      font-weight: 850;
    }

    .rca-scope-line {
      margin: 6px 0 0;
      color: var(--muted-strong);
      font-size: 12px;
      line-height: 1.35;
      font-weight: 700;
    }

    .rca-scope-line strong {
      color: var(--accent-strong);
      font-weight: 950;
    }

    .rca-compact-list {
      margin: 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 6px;
    }

    .rca-compact-list li {
      padding: 7px 8px;
      border-left: 3px solid #7fbfb3;
      border-radius: 6px;
      background: #ffffff;
      color: var(--muted-strong);
      font-size: 12px;
      line-height: 1.35;
    }

    .rca-focus-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-top: 8px;
    }

    .rca-focus-chips span {
      padding: 4px 7px;
      border: 1px solid #bddbd4;
      border-radius: 999px;
      background: #ffffff;
      color: var(--accent-strong);
      font-size: 11px;
      font-weight: 850;
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

    .answer-banner {
      margin: -2px 0 15px;
      display: grid;
      grid-template-columns: 40px minmax(0, 1fr);
      gap: 11px;
      align-items: start;
      padding: 12px 13px;
      border: 1px solid var(--line);
      border-left: 4px solid var(--accent);
      border-radius: var(--radius);
      background: #f8fbfa;
    }

    .answer.context-summary .answer-banner {
      border-left-color: var(--green);
      background: #f6fbf8;
    }

    .answer.context-runbook .answer-banner {
      border-left-color: var(--blue);
      background: #f6f9ff;
    }

    .answer.context-command .answer-banner {
      border-left-color: var(--purple);
      background: #f8f7ff;
    }

    .answer.context-clarify .answer-banner {
      border-left-color: var(--amber);
      background: #fffaf0;
    }

    .answer.context-action .answer-banner {
      border-left-color: var(--accent);
      background: #f5fbf9;
    }

    .answer-banner-icon {
      width: 40px;
      height: 40px;
      border-radius: var(--radius);
      display: grid;
      place-items: center;
      color: #ffffff;
      background: var(--accent);
      font-size: 12px;
      font-weight: 950;
      letter-spacing: 0.02em;
    }

    .answer.context-summary .answer-banner-icon {
      background: var(--green);
    }

    .answer.context-runbook .answer-banner-icon {
      background: var(--blue);
    }

    .answer.context-command .answer-banner-icon {
      background: var(--purple);
    }

    .answer.context-clarify .answer-banner-icon {
      background: var(--amber);
    }

    .answer-banner-kicker {
      margin: 0 0 3px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 900;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .answer-banner-title {
      margin: 0;
      color: var(--text);
      font-size: 16px;
      line-height: 1.25;
      font-weight: 900;
    }

    .answer-banner-subtitle {
      margin: 4px 0 0;
      color: var(--muted-strong);
      font-size: 13px;
      line-height: 1.45;
    }

    .answer-section-title {
      margin: 16px 0 8px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--accent-strong);
      font-size: 13px;
      font-weight: 900;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .answer-section-title::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: var(--accent);
    }

    .answer-field {
      margin: 8px 0;
      display: grid;
      grid-template-columns: minmax(130px, 190px) minmax(0, 1fr);
      gap: 10px;
      align-items: start;
      padding: 10px 11px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface-soft);
    }

    .answer-field-label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .answer-field-value {
      color: var(--text);
      font-weight: 720;
      overflow-wrap: anywhere;
    }

    .answer-chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      align-items: center;
    }

    .answer-mini-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 26px;
      padding: 3px 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #ffffff;
      color: var(--muted-strong);
      font-size: 12px;
      font-weight: 850;
      white-space: nowrap;
    }

    .answer-mini-chip .chip-key {
      color: var(--muted);
      font-weight: 800;
    }

    .answer-mini-chip .chip-value {
      color: var(--text);
      font-weight: 950;
    }

    .answer-mini-chip.critical {
      border-color: #f3b9b5;
      background: var(--red-soft);
    }

    .answer-mini-chip.error {
      border-color: #f2c59e;
      background: #fce7d5;
    }

    .answer-mini-chip.warning {
      border-color: #f2d58a;
      background: var(--amber-soft);
    }

    .answer-mini-chip.info {
      border-color: #b9c9ed;
      background: var(--blue-soft);
    }

    .finding-card {
      margin: 10px 0;
      padding: 11px 12px;
      border: 1px solid var(--line);
      border-left: 4px solid var(--blue);
      border-radius: var(--radius);
      background: #ffffff;
      box-shadow: 0 5px 14px rgba(21, 32, 27, 0.04);
    }

    .finding-card.critical {
      border-left-color: var(--red);
      background: #fff8f7;
    }

    .finding-card.error {
      border-left-color: #c86412;
      background: #fff9f4;
    }

    .finding-card.warning {
      border-left-color: var(--amber);
      background: #fffdf7;
    }

    .finding-card.info {
      border-left-color: var(--blue);
      background: #f8fbff;
    }

    .finding-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      align-items: center;
      margin-bottom: 7px;
    }

    .finding-index {
      color: var(--muted);
      font-size: 12px;
      font-weight: 900;
    }

    .finding-location {
      min-width: 0;
      color: var(--text);
      font-size: 13px;
      font-weight: 900;
      overflow-wrap: anywhere;
    }

    .finding-type {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 2px 7px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--surface-soft);
      color: var(--muted-strong);
      font-size: 12px;
      font-weight: 850;
    }

    .finding-message {
      margin: 0;
      color: var(--muted-strong);
      line-height: 1.52;
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

    .command-card.verify,
    .command-card.check {
      border-color: #bfd9d2;
      border-left-color: var(--accent);
    }

    .command-card.investigate,
    .command-card.analyze {
      border-color: #bcc9ea;
      border-left-color: var(--blue);
      background: #f8fbff;
    }

    .command-card.remediate,
    .command-card.fix {
      border-color: #f1b7b2;
      border-left-color: var(--red);
      background: #fff8f7;
    }

    .command-card.validate {
      border-color: #badbc8;
      border-left-color: var(--green);
      background: #f7fcf9;
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

    .command-card.investigate .command-head,
    .command-card.analyze .command-head {
      background: var(--blue-soft);
      border-bottom-color: #cbd8f2;
    }

    .command-card.remediate .command-head,
    .command-card.fix .command-head {
      background: var(--red-soft);
      border-bottom-color: #f0c4c0;
    }

    .command-card.validate .command-head {
      background: var(--green-soft);
      border-bottom-color: #cde7d8;
    }

    .phase {
      color: var(--accent-strong);
      font-size: 12px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .command-card.investigate .phase,
    .command-card.analyze .phase {
      color: var(--blue);
    }

    .command-card.remediate .phase,
    .command-card.fix .phase {
      color: var(--red);
    }

    .command-card.validate .phase {
      color: var(--green);
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

    .composer-left {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .composer-link {
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #ffffff;
      color: var(--accent-strong);
      min-height: 34px;
      padding: 0 11px;
      font-size: 12px;
      font-weight: 850;
      cursor: pointer;
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
      display: flex;
      flex-direction: column;
      gap: 10px;
      min-width: 0;
      height: 100vh;
      overflow: hidden;
      overscroll-behavior: contain;
    }

    .rail-tabs {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      flex: 0 0 auto;
      padding: 4px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #eef3f2;
    }

    .rail-tab {
      min-width: 0;
      min-height: 36px;
      border: 0;
      border-radius: calc(var(--radius) - 2px);
      background: transparent;
      color: var(--muted-strong);
      cursor: pointer;
      font-size: 12px;
      font-weight: 950;
    }

    .rail-tab.is-active {
      background: var(--surface);
      color: var(--accent-strong);
      box-shadow: 0 1px 4px rgba(17, 24, 39, 0.08);
    }

    .rail-panel {
      flex: 1 1 auto;
      min-height: 0;
      overflow-y: auto;
      overflow-x: hidden;
      padding-right: 4px;
      display: none;
      gap: 10px;
      overscroll-behavior: contain;
    }

    .rail-panel.is-active {
      display: flex;
      flex-direction: column;
      align-content: stretch;
    }

    .rail-section {
      flex: 0 0 auto;
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

    .rail-section.alerts-section {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .alerts-section .alert-list {
      max-height: 230px;
    }

    .insight-rail .rca-workspace {
      flex: 0 0 auto;
      width: 100%;
      margin: 0;
      box-shadow: var(--shadow-soft);
    }

    .insight-rail .rca-workspace-head {
      padding: 12px;
      grid-template-columns: minmax(0, 1fr);
    }

    .insight-rail .rca-confidence-pill {
      justify-self: start;
      min-width: 82px;
    }

    .insight-rail .rca-workspace-grid,
    .insight-rail .rca-workspace-result {
      grid-template-columns: 1fr;
    }

    .insight-rail .rca-workspace-result {
      max-height: 360px;
      overflow-y: auto;
      overscroll-behavior: contain;
    }

    .insight-rail .rca-workspace-actions {
      display: grid;
      grid-template-columns: 1fr;
    }

    .insight-rail .rca-workspace-button {
      width: 100%;
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

    .rca-card {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .rca-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;
    }

    .rca-head strong {
      display: block;
      color: var(--text);
      font-size: 13px;
      line-height: 1.25;
    }

    .rca-head small {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
    }

    .rca-confidence {
      min-width: 54px;
      padding: 5px 7px;
      border-radius: var(--radius);
      background: var(--blue-soft);
      color: var(--blue);
      text-align: center;
      font-size: 17px;
      line-height: 1;
      font-weight: 950;
    }

    .rca-cause {
      padding: 9px;
      border: 1px solid #cbd8f2;
      border-left: 3px solid var(--blue);
      border-radius: var(--radius);
      background: #f8fbff;
      color: var(--text);
      font-size: 12px;
      line-height: 1.4;
      font-weight: 760;
    }

    .rca-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .rca-list span {
      color: var(--muted);
      font-size: 10px;
      font-weight: 950;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .rca-list p {
      margin: 0;
      padding: 7px 8px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface-soft);
      color: var(--muted-strong);
      font-size: 11px;
      line-height: 1.35;
    }

    .rca-action {
      width: 100%;
      min-height: 30px;
      border: 1px solid #8fc9bf;
      border-radius: var(--radius);
      background: var(--accent);
      color: #ffffff;
      font-size: 12px;
      font-weight: 950;
      cursor: pointer;
    }

    .rca-action:hover {
      background: var(--accent-strong);
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

    .control-list {
      gap: 9px;
    }

    .runtime-control-card {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface-soft);
    }

    .runtime-control-card:focus-within {
      border-color: #8fc9bf;
      box-shadow: 0 0 0 3px rgba(15, 139, 125, 0.12);
    }

    .runtime-control-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 9px;
      min-width: 0;
    }

    .runtime-control-head strong {
      display: block;
      color: var(--text);
      font-size: 13px;
      line-height: 1.25;
    }

    .runtime-control-head small {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
    }

    .switch {
      width: 46px;
      height: 26px;
      border: 1px solid var(--line-strong);
      border-radius: 999px;
      background: #dfe6eb;
      padding: 2px;
      cursor: pointer;
      transition: background 0.16s ease, border-color 0.16s ease;
    }

    .switch span {
      display: block;
      width: 20px;
      height: 20px;
      border-radius: 999px;
      background: #ffffff;
      box-shadow: 0 2px 7px rgba(21, 32, 27, 0.18);
      transition: transform 0.16s ease;
    }

    .switch.is-on {
      border-color: #51aa86;
      background: #1f9d68;
    }

    .switch.is-on span {
      transform: translateX(20px);
    }

    .switch:disabled,
    .control-save:disabled {
      cursor: wait;
      opacity: 0.62;
    }

    .interval-control {
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
    }

    .interval-control input {
      width: 100%;
      min-height: 34px;
      border: 1px solid var(--line-strong);
      border-radius: 6px;
      background: #ffffff;
      color: var(--text);
      padding: 6px 9px;
      font: inherit;
      font-size: 13px;
      outline: none;
    }

    .interval-control input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(15, 139, 125, 0.12);
    }

    .control-save {
      min-height: 34px;
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #ffffff;
      cursor: pointer;
      padding: 0 11px;
      font-size: 12px;
      font-weight: 900;
    }

    .control-save:hover {
      background: var(--accent-strong);
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

    .control-badge.live {
      color: var(--green);
      background: var(--green-soft);
    }

    .control-badge.off {
      color: var(--muted-strong);
      background: var(--surface-strong);
    }

    .control-badge.paused {
      color: var(--amber);
      background: var(--amber-soft);
    }

    .control-badge.dry-run,
    .control-badge.disabled {
      color: var(--amber);
      background: var(--amber-soft);
    }

    .control-badge.misconfigured,
    .control-badge.worker-down,
    .control-badge.error {
      color: var(--red);
      background: var(--red-soft);
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
        height: min(58vh, 620px);
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
        height: min(62vh, 640px);
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

      .answer-banner,
      .answer-field {
        grid-template-columns: 1fr;
      }

      .answer-banner-icon {
        width: 34px;
        height: 34px;
      }

      .answer-field-label {
        margin-bottom: -3px;
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
          <button class="quick" type="button" data-prompt="sinh log su co broadcast loop roi phan tich RCA"><span class="icon">A</span><span>RCA incident</span></button>
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
          <textarea id="prompt" rows="2" placeholder="Hỏi agent về log, RCA, alert, report, command xử lý hoặc runtime control..."></textarea>
          <div class="composer-actions">
            <div class="composer-left">
              <label class="toggle">
                <input id="dry-run" type="checkbox" checked>
                Preview only
              </label>
              <button id="new-chat" class="composer-link" type="button">New chat</button>
            </div>
            <button id="send" class="send" type="submit"><span>Send</span><span>›</span></button>
          </div>
        </form>
      </footer>
    </main>

    <aside class="insight-rail">
      <div class="rail-tabs" role="tablist" aria-label="Right panel">
        <button class="rail-tab is-active" type="button" role="tab" aria-selected="true" aria-controls="rail-panel-sentinel" data-rail-tab="sentinel">Log Sentinel</button>
        <button class="rail-tab" type="button" role="tab" aria-selected="false" aria-controls="rail-panel-rca" data-rail-tab="rca">RCA</button>
      </div>

      <div id="rail-panel-sentinel" class="rail-panel is-active" role="tabpanel" data-rail-panel="sentinel">
      <section class="rail-section alerts-section">
        <h3>Priority queue</h3>
        <div id="alert-list" class="alert-list">
          <p class="empty">No alert context loaded yet.</p>
        </div>
      </section>

      <section class="rail-section">
        <h3>Runtime controls</h3>
        <div class="control-list">
          <article class="runtime-control-card">
            <div class="runtime-control-head">
              <div>
                <strong>Telegram alerts</strong>
                <small id="control-telegram-detail">Realtime alert delivery</small>
              </div>
              <span id="control-telegram" class="control-badge disabled">-</span>
            </div>
            <button class="switch" type="button" data-runtime-control="telegram_alerts" aria-label="Toggle Telegram alerts" aria-checked="false"><span></span></button>
          </article>
          <article class="runtime-control-card">
            <div class="runtime-control-head">
              <div>
                <strong>Gmail reports</strong>
                <small id="control-email-detail">Scheduled report delivery</small>
              </div>
              <span id="control-email" class="control-badge disabled">-</span>
            </div>
            <button class="switch" type="button" data-runtime-control="email_reports" aria-label="Toggle Gmail reports" aria-checked="false"><span></span></button>
          </article>
          <article class="runtime-control-card">
            <div class="runtime-control-head">
              <div>
                <strong>Log generator</strong>
                <small id="control-loggen-detail">Synthetic runtime log stream</small>
              </div>
              <span id="control-loggen" class="control-badge disabled">-</span>
            </div>
            <button class="switch" type="button" data-runtime-control="log_generation" aria-label="Toggle log generator" aria-checked="false"><span></span></button>
          </article>
          <article class="runtime-control-card">
            <div class="runtime-control-head">
              <div>
                <strong>Incident generator</strong>
                <small id="control-incident-detail">All RCA incident scenarios</small>
              </div>
              <span id="control-incident" class="control-badge disabled">-</span>
            </div>
            <button class="switch" type="button" data-runtime-control="incident_generation" aria-label="Toggle incident generator" aria-checked="false"><span></span></button>
          </article>
          <article class="runtime-control-card">
            <div class="runtime-control-head">
              <div>
                <strong>Generator interval</strong>
                <small id="control-interval-detail">Seconds between generated logs</small>
              </div>
              <span id="control-interval" class="control-badge live">-</span>
            </div>
            <div class="interval-control">
              <input id="control-interval-input" type="number" min="1" max="86400" step="1" inputmode="numeric" aria-label="Generator interval seconds">
              <button id="control-interval-save" class="control-save" type="button">Save</button>
            </div>
          </article>
          <article class="runtime-control-card">
            <div class="runtime-control-head">
              <div>
                <strong>Incident interval</strong>
                <small id="control-incident-interval-detail">Seconds between all-scenario incident packs</small>
              </div>
              <span id="control-incident-interval" class="control-badge live">-</span>
            </div>
            <div class="interval-control">
              <input id="control-incident-interval-input" type="number" min="1" max="86400" step="1" inputmode="numeric" aria-label="Incident generator interval seconds">
              <button id="control-incident-interval-save" class="control-save" type="button">Save</button>
            </div>
          </article>
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
      </div>

      <div id="rail-panel-rca" class="rail-panel" role="tabpanel" data-rail-panel="rca" hidden>
        <section class="rca-workspace" aria-label="RCA workspace">
          <div class="rca-workspace-head">
            <div>
              <p class="rca-workspace-kicker">RCA workspace</p>
              <h3 class="rca-workspace-title">Basic RCA Search</h3>
            </div>
            <div id="rca-workspace-confidence" class="rca-confidence-pill">--<span>confidence</span></div>
          </div>
          <div class="rca-workspace-grid">
            <label class="rca-field">
              Impact / symptom
              <textarea id="rca-impact" rows="3"></textarea>
            </label>
            <div class="rca-field-stack">
              <label class="rca-field">
                Window (hours)
                <input id="rca-lookback" type="number" min="0.25" max="168" step="0.25">
              </label>
              <label class="rca-field">
                From
                <input id="rca-start" type="datetime-local">
              </label>
              <label class="rca-field">
                To
                <input id="rca-end" type="datetime-local">
              </label>
            </div>
          </div>
          <div class="rca-workspace-actions">
            <button id="rca-analyze" class="rca-workspace-button" type="button">Analyze Current Logs</button>
            <button id="rca-send-chat" class="rca-workspace-button secondary" type="button">Send As Chat</button>
            <button id="rca-clear" class="rca-workspace-button danger" type="button">Clear</button>
          </div>
          <div id="rca-workspace-result" class="rca-workspace-result">
            <div class="rca-result-block">
              <h4>Result</h4>
              <p class="rca-root-cause">No RCA search has been run in this tab.</p>
            </div>
            <div class="rca-result-block">
              <h4>Evidence & Action</h4>
              <ul class="rca-compact-list">
                <li>Enter impact or choose an incident scenario, then run RCA.</li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    </aside>
  </div>

  <script>
    const conversation = document.getElementById("conversation");
    const form = document.getElementById("chat-form");
    const promptBox = document.getElementById("prompt");
    const dryRunBox = document.getElementById("dry-run");
    const sendButton = document.getElementById("send");
    let conversationId = getConversationId();

    const state = {
      busy: false,
      rcaScenarios: [],
      rcaWorkspaceHasRun: false,
      rcaWorkspaceAnalysis: null
    };

    function getConversationId() {
      const key = "infra-log-sentinel-web-session";
      try {
        const existing = window.localStorage.getItem(key);
        if (existing) {
          return existing;
        }
        const generated = newConversationId();
        window.localStorage.setItem(key, generated);
        return generated;
      } catch (error) {
        return newConversationId();
      }
    }

    function newConversationId() {
      return window.crypto && window.crypto.randomUUID
        ? "web-" + window.crypto.randomUUID()
        : "web-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
    }

    function startNewChatSession() {
      const key = "infra-log-sentinel-web-session";
      conversationId = newConversationId();
      try {
        window.localStorage.setItem(key, conversationId);
      } catch (error) {
        // Ignore storage failures; the in-memory id still separates this browser session.
      }
      conversation.innerHTML = "";
      appendMessage("agent", "**New chat.** Mình đã tách ngữ cảnh hội thoại. Câu tiếp theo sẽ được xử lý như một Log Sentinel/RCA investigation mới.");
      promptBox.focus();
    }

    function switchRailTab(target) {
      const tabName = target === "rca" ? "rca" : "sentinel";
      document.querySelectorAll("[data-rail-tab]").forEach(function(tab) {
        const active = tab.dataset.railTab === tabName;
        tab.classList.toggle("is-active", active);
        tab.setAttribute("aria-selected", active ? "true" : "false");
      });
      document.querySelectorAll("[data-rail-panel]").forEach(function(panel) {
        const active = panel.dataset.railPanel === tabName;
        panel.classList.toggle("is-active", active);
        panel.hidden = !active;
      });
    }

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
      html = html.replace(/\b(Running|Stopped|Paused|Enabled|Disabled)\b/gi, function(status) {
        const key = status.toLowerCase();
        const cls = key === "running" || key === "enabled" ? "info" : key === "paused" ? "warning" : "error";
        return '<span class="answer-mini-chip ' + cls + '">' + status + '</span>';
      });
      html = html.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noreferrer">$1</a>');
      return html;
    }

    function renderAgentContent(text) {
      const normalized = String(text || "").replace(/\r\n/g, "\n");
      const context = classifyAgentAnswer(normalized);
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

      return '<div class="answer context-' + context.type + '">' + renderAnswerBanner(context) + parts.join("") + '</div>';
    }

    function textKey(value) {
      return String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
    }

    function classifyAgentAnswer(text) {
      const key = textKey(text);
      if (key.includes("aiops rca investigation") || key.includes("aiops rca brief") || key.includes("root cause:") || key.includes("event timeline:")) {
        return {
          type: "rca",
          icon: "RCA",
          kicker: "Response type",
          title: "Root cause investigation",
          subtitle: "Root cause, impact, timeline, evidence and actions are grouped for incident review."
        };
      }
      if (key.includes("runbook command") || key.includes("command de xuat") || (key.includes("verify:") && key.includes("remediate:"))) {
        return {
          type: "runbook",
          icon: "RB",
          kicker: "Response type",
          title: "Runbook recommendation",
          subtitle: "Commands are grouped by phase so verification stays separate from remediation."
        };
      }
      if (key.includes("giai thich") || key.includes("command insight") || key.includes("dung de lam gi") || key.includes("khong phai yeu cau sinh them runbook")) {
        return {
          type: "command",
          icon: "CMD",
          kicker: "Response type",
          title: "Command explanation",
          subtitle: "Purpose, usage and operational risk are separated for quick review."
        };
      }
      if (key.includes("tom tat") || key.includes("tong so event") || key.includes("top alert") || key.includes("theo severity") || key.includes("theo domain")) {
        return {
          type: "summary",
          icon: "SUM",
          kicker: "Response type",
          title: "Log intelligence summary",
          subtitle: "Signal, severity and priority findings are organized for scanning."
        };
      }
      if (key.includes("thieu ngu canh") || key.includes("vui long noi ro") || key.includes("can lam ro") || key.includes("hoi lai truoc")) {
        return {
          type: "clarify",
          icon: "?",
          kicker: "Response type",
          title: "Needs clarification",
          subtitle: "The agent is asking for missing target, value, time window or delivery channel."
        };
      }
      if (key.includes("da tao") || key.includes("da gui") || key.includes("da cap nhat") || key.includes("runtime") || key.includes("telegram") || key.includes("gmail")) {
        return {
          type: "action",
          icon: "OK",
          kicker: "Response type",
          title: "Action result",
          subtitle: "Execution details and state changes are grouped below."
        };
      }
      if (key.includes("xin chao")) {
        return {
          type: "action",
          icon: "AI",
          kicker: "Copilot ready",
          title: "Infrastructure Log Sentinel",
          subtitle: "Ask about logs, reports, commands or runtime controls."
        };
      }
      return {
        type: "analysis",
        icon: "AI",
        kicker: "Response type",
        title: "Operational analysis",
        subtitle: "The answer is structured into readable findings and details."
      };
    }

    function renderAnswerBanner(context) {
      return '' +
        '<div class="answer-banner">' +
          '<div class="answer-banner-icon">' + escapeHtml(context.icon) + '</div>' +
          '<div>' +
            '<p class="answer-banner-kicker">' + escapeHtml(context.kicker) + '</p>' +
            '<p class="answer-banner-title">' + escapeHtml(context.title) + '</p>' +
            '<p class="answer-banner-subtitle">' + escapeHtml(context.subtitle) + '</p>' +
          '</div>' +
        '</div>';
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

        const sectionTitle = parseSectionTitle(line);
        if (sectionTitle) {
          flushList();
          html.push('<div class="answer-section-title">' + inlineFormat(sectionTitle) + '</div>');
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
          const special = renderSpecialLine(bullet[1]);
          if (special) {
            flushList();
            html.push(special);
            continue;
          }
          if (listType !== "ul") {
            flushList();
            listType = "ul";
          }
          listItems.push(bullet[1]);
          continue;
        }

        const numbered = line.match(/^(\d+)\.\s+(.+)$/);
        if (numbered) {
          const special = renderSpecialLine(numbered[2], numbered[1]);
          if (special) {
            flushList();
            html.push(special);
            continue;
          }
          if (listType !== "ol") {
            flushList();
            listType = "ol";
          }
          listItems.push(numbered[2]);
          continue;
        }

        const field = parseKeyValueLine(line);
        if (field && shouldPromoteField(field)) {
          flushList();
          html.push(renderFieldCard(field.label, field.value));
          continue;
        }

        flushList();
        html.push('<p>' + inlineFormat(line) + '</p>');
      }

      flushList();
      flushTable();
      return html.join("");
    }

    function parseSectionTitle(line) {
      const trimmed = String(line || "").trim();
      if (!trimmed.endsWith(":") || trimmed.includes("://")) {
        return "";
      }
      const title = trimmed.slice(0, -1).trim();
      if (title.length < 2 || title.length > 56 || title.includes("|")) {
        return "";
      }
      return title;
    }

    function renderSpecialLine(line, index) {
      const finding = parseFindingLine(line, index);
      if (finding) {
        return renderFindingCard(finding);
      }
      const field = parseKeyValueLine(line);
      if (field && shouldPromoteField(field)) {
        return renderFieldCard(field.label, field.value);
      }
      return "";
    }

    function parseFindingLine(line, index) {
      const detailed = String(line || "").match(/^\[([A-Za-z]+)\]\s+(\S+)\s+([^:]+):\s*(.+)$/);
      if (detailed) {
        return {
          index: index || "",
          severity: detailed[1],
          location: detailed[2],
          type: detailed[3],
          message: detailed[4]
        };
      }
      const compact = String(line || "").match(/^\[([A-Za-z]+)\]\s+(.+?)\s+-\s+(.+)$/);
      if (compact) {
        return {
          index: index || "",
          severity: compact[1],
          location: compact[2],
          type: compact[3],
          message: ""
        };
      }
      return null;
    }

    function renderFindingCard(finding) {
      const severity = severityClass(finding.severity);
      const index = finding.index ? '<span class="finding-index">#' + escapeHtml(finding.index) + '</span>' : "";
      const message = finding.message ? '<p class="finding-message">' + inlineFormat(finding.message) + '</p>' : "";
      return '' +
        '<article class="finding-card ' + severity + '">' +
          '<div class="finding-meta">' +
            index +
            '<span class="severity ' + severity + '">' + escapeHtml(String(finding.severity || "info").toUpperCase()) + '</span>' +
            '<span class="finding-location">' + inlineFormat(finding.location || "-") + '</span>' +
            '<span class="finding-type">' + inlineFormat(finding.type || "-") + '</span>' +
          '</div>' +
          message +
        '</article>';
    }

    function parseKeyValueLine(line) {
      const match = String(line || "").match(/^([^:]{2,48}):\s*(.+)$/);
      if (!match) {
        return null;
      }
      const label = match[1].trim();
      const value = match[2].trim();
      if (!label || !value || label.includes("://") || label.includes("|")) {
        return null;
      }
      return { label: label, value: value };
    }

    function shouldPromoteField(field) {
      const label = textKey(field.label);
      if (label.includes("http")) {
        return false;
      }
      return (
        label.includes("tong") ||
        label.includes("severity") ||
        label.includes("domain") ||
        label.includes("file") ||
        label.includes("pham vi") ||
        label.includes("log") ||
        label.includes("huong xu ly") ||
        label.includes("question") ||
        label.includes("command") ||
        label.includes("intent") ||
        label.includes("risk") ||
        label.includes("summary") ||
        label.includes("nguyen nhan") ||
        label.includes("tac dong")
      );
    }

    function renderFieldCard(label, value) {
      return '' +
        '<div class="answer-field">' +
          '<div class="answer-field-label">' + inlineFormat(label) + '</div>' +
          '<div class="answer-field-value">' + renderFieldValue(value) + '</div>' +
        '</div>';
    }

    function renderFieldValue(value) {
      const pairs = parseValuePairs(value);
      if (pairs.length) {
        return '<div class="answer-chip-row">' + pairs.map(renderValueChip).join("") + '</div>';
      }
      return inlineFormat(value);
    }

    function parseValuePairs(value) {
      const trimmed = String(value || "").trim();
      if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
        const body = trimmed.slice(1, -1);
        const pairs = [];
        const regex = /['"]?([^'",:{}]+)['"]?\s*:\s*['"]?([^,'"}]+)['"]?/g;
        let match;
        while ((match = regex.exec(body)) !== null) {
          pairs.push({ key: match[1].trim(), value: match[2].trim() });
        }
        return pairs;
      }
      if (/^[A-Za-z_, -]+$/.test(trimmed) && trimmed.includes(",")) {
        return trimmed.split(",").map(function(item) {
          return { key: item.trim(), value: "" };
        }).filter(function(item) {
          return item.key;
        });
      }
      return [];
    }

    function renderValueChip(pair) {
      const severity = severityClass(pair.key);
      const value = pair.value ? '<span class="chip-value">' + inlineFormat(pair.value) + '</span>' : "";
      return '' +
        '<span class="answer-mini-chip ' + severity + '">' +
          '<span class="chip-key">' + inlineFormat(pair.key) + '</span>' +
          value +
        '</span>';
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
      const phaseKey = phaseClass(phase);
      return '' +
        '<div class="command-card ' + phaseKey + '">' +
          '<div class="command-head"><span class="phase">' + escapeHtml(phase) + '</span><button class="command-copy" type="button" data-copy="command">Copy</button></div>' +
          '<code class="command-text">' + escapeHtml(String(command || "").trim()) + '</code>' +
        '</div>';
    }

    function phaseClass(phase) {
      const key = String(phase || "").toLowerCase();
      if (["verify", "investigate", "remediate", "validate", "check", "analyze", "fix"].includes(key)) {
        return key;
      }
      return "verify";
    }

    function appendMessage(role, text, extraClass) {
      const row = document.createElement("div");
      row.className = "message " + role + (extraClass ? " " + extraClass : "");

      const avatar = document.createElement("div");
      avatar.className = "avatar";
      avatar.textContent = role === "user" ? "ME" : "AI";

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      if (role === "agent") {
        bubble.innerHTML = extraClass === "typing"
          ? '<div class="typing-line">' + escapeHtml(text) + '</div>'
          : renderAgentContent(text);
      } else {
        bubble.innerHTML = linkify(text);
      }

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
            conversation_id: conversationId,
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

    function controlViewState(control, delivery) {
      const paused = Boolean(control && control.paused);
      const manualOff = Boolean(control && control.manual_off);
      if (delivery) {
        return {
          state: delivery.state || "disabled",
          label: delivery.label || delivery.state || "unknown",
          detail: delivery.detail || "",
          enabled: !paused
        };
      }
      if (manualOff) {
        return {
          state: "off",
          label: "off",
          detail: "Disabled until it is enabled again.",
          enabled: false
        };
      }
      if (paused) {
        return {
          state: "paused",
          label: "paused",
          detail: control.paused_until ? "Paused until " + control.paused_until : "Paused.",
          enabled: false
        };
      }
      return {
        state: "live",
        label: "on",
        detail: "Enabled.",
        enabled: true
      };
    }

    function controlBadgeClass(state) {
      const value = String(state || "").toLowerCase().replace(/_/g, "-");
      if (["live", "off", "paused", "dry-run", "disabled", "misconfigured", "worker-down", "error"].includes(value)) {
        return value;
      }
      return "disabled";
    }

    function updateControlWidget(uiKey, controlName, viewState) {
      const badge = document.getElementById("control-" + uiKey);
      const detail = document.getElementById("control-" + uiKey + "-detail");
      const toggle = document.querySelector('[data-runtime-control="' + controlName + '"]');
      if (badge) {
        badge.className = "control-badge " + controlBadgeClass(viewState.state);
        badge.textContent = viewState.label;
        badge.title = viewState.detail || "";
      }
      if (detail) {
        detail.textContent = viewState.detail || "Runtime control";
      }
      if (toggle) {
        toggle.classList.toggle("is-on", Boolean(viewState.enabled));
        toggle.setAttribute("aria-checked", viewState.enabled ? "true" : "false");
        toggle.title = viewState.enabled ? "Turn off" : "Turn on";
      }
    }

    function updateRuntimeControls(status) {
      const pauses = (status.runtime_controls && status.runtime_controls.pauses) || {};
      const delivery = status.delivery || {};
      updateControlWidget(
        "telegram",
        "telegram_alerts",
        controlViewState(pauses.telegram_alerts, delivery.telegram_alerts)
      );
      updateControlWidget("email", "email_reports", controlViewState(pauses.email_reports));
      updateControlWidget("loggen", "log_generation", controlViewState(pauses.log_generation));
      updateControlWidget("incident", "incident_generation", controlViewState(pauses.incident_generation));

      const config = status.config || {};
      const values = (status.runtime_controls && status.runtime_controls.values) || {};
      const interval = values.demo_log_interval_seconds || config.demo_log_interval_seconds || "";
      setText("control-interval", interval ? String(interval) + "s" : "-");
      const intervalInput = document.getElementById("control-interval-input");
      if (intervalInput && document.activeElement !== intervalInput) {
        intervalInput.value = interval || "";
      }
      const incidentInterval = values.incident_log_interval_seconds || config.incident_log_interval_seconds || "";
      setText("control-incident-interval", incidentInterval ? String(incidentInterval) + "s" : "-");
      const incidentIntervalInput = document.getElementById("control-incident-interval-input");
      if (incidentIntervalInput && document.activeElement !== incidentIntervalInput) {
        incidentIntervalInput.value = incidentInterval || "";
      }
    }

    function setRuntimeControlsBusy(value) {
      document.querySelectorAll("[data-runtime-control], #control-interval-save, #control-interval-input, #control-incident-interval-save, #control-incident-interval-input").forEach(function(element) {
        element.disabled = value;
      });
    }

    async function updateRuntimeControl(payload) {
      setRuntimeControlsBusy(true);
      try {
        const response = await fetch("/runtime-controls", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (!response.ok) {
          throw new Error(result.message || result.error || "Runtime control update failed");
        }
        await refreshStatus();
      } catch (error) {
        appendMessage("agent", "Không cập nhật được runtime control: " + error.message);
      } finally {
        setRuntimeControlsBusy(false);
      }
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

    function renderRcaWorkspace(rca) {
      const scenarios = (rca && rca.available_log_scenarios) || [];
      updateRcaScenarioOptions(scenarios);
      if (!state.rcaWorkspaceHasRun) {
        renderRcaWorkspaceEmpty();
        return;
      }
      renderRcaWorkspaceAnalysis(state.rcaWorkspaceAnalysis);
    }

    function renderRcaWorkspaceEmpty(message) {
      const confidence = document.getElementById("rca-workspace-confidence");
      const result = document.getElementById("rca-workspace-result");
      if (!confidence || !result) {
        return;
      }
      const resultMessage = message || "No RCA search has been run in this tab.";
      const actionMessage = message
        ? "The previous RCA result was cleared. Run Analyze Current Logs to search the current incident log corpus."
        : "Turn on Incident generator in Runtime controls to keep all incident scenarios in current logs, then run Analyze Current Logs.";
      confidence.innerHTML = '--<span>confidence</span>';
      result.innerHTML = '' +
        '<div class="rca-result-block">' +
          '<h4>Result</h4>' +
          '<p class="rca-root-cause">' + escapeHtml(resultMessage) + '</p>' +
        '</div>' +
        '<div class="rca-result-block">' +
          '<h4>Evidence & Action</h4>' +
          '<ul class="rca-compact-list"><li>' + escapeHtml(actionMessage) + '</li></ul>' +
        '</div>';
    }

    function updateRcaScenarioOptions(scenarios) {
      const select = document.getElementById("rca-scenario");
      if (!select || !scenarios.length) {
        return;
      }
      const current = select.value;
      const key = scenarios.join("|");
      if (state.rcaScenarios.join("|") === key) {
        return;
      }
      state.rcaScenarios = scenarios.slice();
      select.innerHTML = scenarios.map(function(name) {
        return '<option value="' + escapeHtml(name) + '">' + escapeHtml(name) + '</option>';
      }).join("");
      if (scenarios.includes(current)) {
        select.value = current;
      }
    }

    function renderRcaWorkspaceAnalysis(analysis) {
      const confidence = document.getElementById("rca-workspace-confidence");
      const result = document.getElementById("rca-workspace-result");
      if (!confidence || !result) {
        return;
      }
      if (!analysis || !analysis.incident_id || analysis.incident_id === "LOG-RCA-NONE") {
        const emptyScope = analysis && analysis.scope_label ? String(analysis.scope_label) : "selected log window";
        confidence.innerHTML = '--<span>confidence</span>';
        result.innerHTML = '' +
          '<div class="rca-result-block">' +
            '<h4>Result</h4>' +
            '<p class="rca-root-cause">No RCA candidate found from the selected log window.</p>' +
            '<p class="rca-scope-line"><strong>Scope:</strong> ' + escapeHtml(emptyScope) + '</p>' +
          '</div>' +
          '<div class="rca-result-block">' +
            '<h4>Evidence & Action</h4>' +
            '<ul class="rca-compact-list"><li>Widen the time window or provide a more specific impact/symptom.</li></ul>' +
          '</div>';
        return;
      }
      confidence.innerHTML = String(analysis.confidence ?? 0) + '%<span>confidence</span>';
      const actions = analysis.recommended_actions || {};
      const evidence = (analysis.evidence || []).slice(0, 4);
      const immediate = (actions.immediate_actions || []).slice(0, 3);
      const focusTerms = (analysis.focus_terms || []).slice(0, 6);
      const timeline = (analysis.timeline || []).slice(0, 3);
      const scenarioLabel = String(analysis.workspace_scenario || analysis.scenario || "");
      const modeLabel = analysis.workspace_mode === "generated_incident"
        ? "generated incident"
        : analysis.workspace_mode === "current_logs"
          ? "current logs"
          : "log window";
      const scopeLabel = String(analysis.scope_label || (scenarioLabel ? "generated " + scenarioLabel + " incident burst" : modeLabel));
      const scenarioScope = scenarioLabel
        ? ' <strong>Scenario:</strong> ' + escapeHtml(scenarioLabel)
        : "";
      const evidenceItems = evidence.length ? evidence : timeline.map(function(item) {
        return [item.timestamp, item.source, item.event_type].filter(Boolean).join(" | ");
      });
      const actionItems = immediate.length ? immediate : ["Collect more evidence before remediation."];
      result.innerHTML = '' +
        '<div class="rca-result-block">' +
          '<h4>Most Likely Root Cause</h4>' +
          '<p class="rca-root-cause">' + escapeHtml(analysis.most_likely_root_cause || analysis.summary || "-") + '</p>' +
          '<p class="rca-scope-line"><strong>Scope:</strong> ' + escapeHtml(scopeLabel) + scenarioScope + '</p>' +
          '<div class="rca-focus-chips">' +
            '<span>' + escapeHtml(String(analysis.severity || "info").toUpperCase()) + '</span>' +
            '<span>' + escapeHtml(String(analysis.status || "-")) + '</span>' +
            '<span>' + String(analysis.correlated_events || 0) + ' events</span>' +
            '<span>' + escapeHtml(modeLabel) + '</span>' +
            focusTerms.map(function(term) { return '<span>' + escapeHtml(term) + '</span>'; }).join("") +
          '</div>' +
        '</div>' +
        '<div class="rca-result-block">' +
          '<h4>Evidence & Action</h4>' +
          '<ul class="rca-compact-list">' +
            evidenceItems.map(function(item) { return '<li>' + escapeHtml(item) + '</li>'; }).join("") +
            actionItems.map(function(item) { return '<li>' + escapeHtml(item) + '</li>'; }).join("") +
          '</ul>' +
        '</div>';
    }

    function setRcaWorkspaceBusy(value) {
      ["rca-analyze", "rca-send-chat", "rca-clear", "rca-impact", "rca-lookback", "rca-start", "rca-end"].forEach(function(id) {
        const element = document.getElementById(id);
        if (element) {
          element.disabled = value;
        }
      });
    }

    function clearRcaWorkspace() {
      const impact = document.getElementById("rca-impact");
      const lookback = document.getElementById("rca-lookback");
      const start = document.getElementById("rca-start");
      const end = document.getElementById("rca-end");
      state.rcaWorkspaceHasRun = false;
      state.rcaWorkspaceAnalysis = null;
      if (impact) {
        impact.value = "";
      }
      if (lookback) {
        lookback.value = "";
      }
      if (start) {
        start.value = "";
      }
      if (end) {
        end.value = "";
      }
      renderRcaWorkspaceEmpty();
      if (impact) {
        impact.focus();
      }
    }

    async function runRcaWorkspace(mode) {
      const impact = document.getElementById("rca-impact").value.trim();
      const lookback = Number(document.getElementById("rca-lookback").value || 1);
      const start = document.getElementById("rca-start").value.trim();
      const end = document.getElementById("rca-end").value.trim();
      const scenarioSelect = document.getElementById("rca-scenario");
      const scenario = scenarioSelect ? scenarioSelect.value || "broadcast_loop" : "broadcast_loop";
      const endpoint = mode === "generate" ? "/rca/logs/generate" : "/rca/logs/analyze";
      const payload = {
        impact: impact,
        lookback_hours: Number.isFinite(lookback) && lookback > 0 ? lookback : 1
      };
      if (start && end) {
        payload.start_time = start;
        payload.end_time = end;
      }
      if (mode === "generate") {
        payload.scenario = scenario;
      }
      setRcaWorkspaceBusy(true);
      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (!response.ok) {
          throw new Error(result.message || result.error || "RCA request failed");
        }
        state.rcaWorkspaceHasRun = true;
        const analysis = result.analysis || {};
        if (mode === "generate") {
          analysis.workspace_mode = "generated_incident";
          analysis.workspace_scenario = String(result.scenario || scenario);
          analysis.scope_label = analysis.scope_label || "generated " + analysis.workspace_scenario + " incident burst";
        } else {
          analysis.workspace_mode = "current_logs";
          analysis.workspace_scenario = "";
          analysis.scope_label = analysis.scope_label || (start && end ? "selected time range" : "last " + String(payload.lookback_hours) + "h");
        }
        state.rcaWorkspaceAnalysis = analysis;
        renderRcaWorkspaceAnalysis(analysis);
        switchRailTab("rca");
        const context = mode === "generate" ? "generated " + scenario : "current logs";
        appendMessage("agent", "RCA workspace updated (" + context + "): " + String(analysis.incident_id || "analysis complete"));
        await refreshStatus();
      } catch (error) {
        appendMessage("agent", "Không chạy được RCA workspace: " + error.message);
      } finally {
        setRcaWorkspaceBusy(false);
      }
    }

    function sendRcaWorkspaceAsChat() {
      const impactBox = document.getElementById("rca-impact");
      const lookbackBox = document.getElementById("rca-lookback");
      const startBox = document.getElementById("rca-start");
      const endBox = document.getElementById("rca-end");
      const impact = impactBox.value.trim();
      const lookback = Number(lookbackBox.value || 0);
      if (!impact) {
        switchRailTab("rca");
        appendMessage("agent", "RCA chat cần impact/symptom trước khi gửi sang agent.");
        impactBox.focus();
        return;
      }
      const windowText = Number.isFinite(lookback) && lookback > 0
        ? " trong " + String(lookback) + " gio"
        : "";
      const rangeText = startBox.value && endBox.value
        ? " tu " + startBox.value + " den " + endBox.value
        : windowText;
      askAgent("phan tich RCA dua tren log hien tai: " + impact + rangeText);
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

        updateRuntimeControls(status);

        renderAlerts(status.top_alerts || []);
        renderRcaWorkspace(status.rca || {});
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
      button.dataset.promptBound = "true";
      button.addEventListener("click", function() {
        askAgent(button.dataset.prompt);
      });
    });

    document.addEventListener("click", function(event) {
      const button = event.target.closest("[data-prompt]");
      if (!button || button.dataset.promptBound === "true") {
        return;
      }
      askAgent(button.dataset.prompt);
    });

    document.querySelectorAll("[data-rail-tab]").forEach(function(tab) {
      tab.addEventListener("click", function() {
        switchRailTab(tab.dataset.railTab);
      });
    });

    document.querySelectorAll("[data-runtime-control]").forEach(function(button) {
      button.addEventListener("click", function() {
        const currentlyEnabled = button.getAttribute("aria-checked") === "true";
        updateRuntimeControl({
          control: button.dataset.runtimeControl,
          enabled: !currentlyEnabled
        });
      });
    });

    document.getElementById("rca-analyze").addEventListener("click", function() {
      runRcaWorkspace("analyze");
    });

    document.getElementById("rca-send-chat").addEventListener("click", function() {
      sendRcaWorkspaceAsChat();
    });

    document.getElementById("rca-clear").addEventListener("click", function() {
      clearRcaWorkspace();
    });

    document.getElementById("new-chat").addEventListener("click", function() {
      startNewChatSession();
    });

    document.getElementById("control-interval-save").addEventListener("click", function() {
      const input = document.getElementById("control-interval-input");
      const seconds = Number(input.value);
      if (!Number.isFinite(seconds) || seconds < 1 || seconds > 86400) {
        appendMessage("agent", "Interval phải nằm trong khoảng 1 đến 86400 giây.");
        input.focus();
        return;
      }
      updateRuntimeControl({
        setting: "demo_log_interval_seconds",
        seconds: seconds
      });
    });

    document.getElementById("control-incident-interval-save").addEventListener("click", function() {
      const input = document.getElementById("control-incident-interval-input");
      const seconds = Number(input.value);
      if (!Number.isFinite(seconds) || seconds < 1 || seconds > 86400) {
        appendMessage("agent", "Incident interval must be between 1 and 86400 seconds.");
        input.focus();
        return;
      }
      updateRuntimeControl({
        setting: "incident_log_interval_seconds",
        seconds: seconds
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
