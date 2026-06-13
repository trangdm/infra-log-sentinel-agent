# GreenNode Submission Packet

Last updated: 2026-06-13

## Project

Infrastructure Log Sentinel Agent is an AI operations copilot for infrastructure log intelligence. It reads Network, Linux, Windows, and VMware logs, classifies severity, explains probable cause and impact, recommends runbook actions, sends realtime Telegram alerts, tracks ACK/escalation, generates PDF reports, and exposes runtime controls through a professional web chat console.

## Links

- Repository: `https://github.com/trangdm/infra-log-sentinel-agent`
- Hosted demo: `https://endpoint-c42c8f0b-6d74-42d5-9d6d-9fc7ce6b49e9.agentbase-runtime.aiplatform.vngcloud.vn`
- Health check: `https://endpoint-c42c8f0b-6d74-42d5-9d6d-9fc7ce6b49e9.agentbase-runtime.aiplatform.vngcloud.vn/health`
- Status API: `https://endpoint-c42c8f0b-6d74-42d5-9d6d-9fc7ce6b49e9.agentbase-runtime.aiplatform.vngcloud.vn/status`
- GreenNode submission page: `https://greennode.ai/events/greennode-claw-a-thon`
- Rulebook: `https://greennode.ai/claw-a-thon-rulebook`
- AgentBase skills: `https://github.com/vngcloud/greennode-agentbase-skills`

## Runtime

- GreenNode AgentBase runtime ID: `runtime-a864917b-1a16-4083-a64c-82f4e79f6602`
- Runtime image: `vcr.vngcloud.vn/111480-abp111815/infra-log-sentinel-agent:v20260613-counter-window-reset-v17`
- Runtime mode: `runtime_folder`
- Port: `8080`
- Required contract: `GET /health`
- Extra demo APIs: `GET /status`, `POST /chat`, `POST /invocations`, `POST /runtime-controls`, `POST /telegram-alert-counters/reset`

## What To Demo

1. Open the hosted endpoint and show the web console.
2. Ask: `tom tat log hom nay`
3. Ask: `hay report o giao dien chat`
4. Ask: `toi khong hieu lenh nay dung de lam gi hay giai thich y nghia "Get-Service SQLAgent"`
5. Toggle runtime controls:
   - Telegram alerts on/off.
   - Gmail reports on/off.
   - Log generator on/off.
   - Edit generator interval and save.
6. Show Telegram alert counters:
   - `Today`
   - `24h`
   - `7d`
   - `All`
   - Reset counters button.
7. Trigger or wait for realtime Telegram alerts and ACK one alert from Telegram.

## Key Capabilities

- Multi-domain log parsing: Network, Linux, Windows, VMware.
- Severity classification: info, warning, error, critical.
- Deterministic operational answers for log summaries, report requests, command explanations, and runtime controls.
- Conversation-aware chat logic so follow-up questions stay connected to prior context.
- Professional web UI with priority queue, status indicators, runtime controls, and Telegram alert counters.
- Telegram realtime alert delivery for warning/error/critical events.
- Telegram ACK handling and escalation timeout flow.
- Gmail PDF report delivery with runtime pause control.
- Self-contained synthetic log generation for reliable hosted demo behavior.

## Verification

Verified after deploying v17 on 2026-06-13:

- `/health`: `ok`
- `/status`: includes `telegram_alert_metrics.windows`
- Default Telegram counter window: `today`
- Runtime timezone: `Asia/Ho_Chi_Minh`
- Telegram delivery: controlled from the Runtime Controls panel; enable it before the realtime Telegram alert demo.
- Runtime scheduler worker: `running`
- UI includes `Today`, `24h`, `7d`, `All`, and `Reset`
- Core regression test in runtime container: `25 passed`

## Security Notes

- `.env`, `.env.greennode`, `.greennode.json`, `.agentbase/`, tokens, runtime data, and generated reports are excluded from git and Docker build context.
- The repository contains examples/templates only; live credentials are not committed.
- The hosted runtime uses GreenNode environment variables for secrets.
