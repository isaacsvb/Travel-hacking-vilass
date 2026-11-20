---
name: browser-collector
description: Opt-in browser-automation collector template for sites with no API. OFF by default and never required for any core capability. Trigger phrases include scrape, browser automation, no API, airline site collector.
category: flights
summary: Opt-in Playwright collector template. Off by default, ToS-risky, never required.
api_key: None (requires explicit opt-in)
---

# Browser Collector (opt-in, off by default)

A template for collecting data from sites that have no usable API. **This is never part of the free-first core path.** Everything the toolkit promises works without any scraping.

## Hard rules

1. **Off by default.** A collector runs only if the operator explicitly enables it for that specific target. If it is not enabled, do not scrape — use the keyless/licensed sources instead.
2. **Respect the site.** Rate-limit per domain, cap concurrency, randomize pacing. Do not hammer.
3. **Isolate sessions.** Fresh browser context per target; no shared cookies across targets unless explicitly configured. Inject credentials from the environment, never hard-code.
4. **Fail loud, not empty.** On a CAPTCHA, block page, or unexpected layout, abort the target and report a structured failure reason. NEVER return empty results that could be read as "no availability."
5. **Same schema out.** Emit the same normalized fields the API sources produce, so downstream logic is source-agnostic.

## Compliance warning (must be shown before enabling)

Scraping airline/portal sites typically violates their Terms of Service and is actively defended against (bot mitigation, CAPTCHAs, device fingerprinting). It can get your account or IP blocked. Enable a collector only for a target you are authorized to automate, and only after acknowledging this risk. Prefer the licensed/free API paths in every other skill.
