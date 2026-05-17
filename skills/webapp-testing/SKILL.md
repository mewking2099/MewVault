---
name: webapp-testing
description: Test local web applications using Playwright — verify frontend functionality, debug UI behavior, capture screenshots, view browser logs. Use when testing a running web app, verifying UI behavior, or debugging frontend issues.
origin: anthropics
---

# Web Application Testing

Test local web apps using native Python Playwright scripts.

## Decision Tree

```
Is it static HTML?
  Yes → Read file directly to find selectors → write Playwright script
  No (dynamic) → Is server running?
    No → Start server first, then test
    Yes → Screenshot/inspect DOM → find selectors → execute actions
```

## Starting a Server + Testing

```python
# with_server pattern (start server, then test)
# Run server in background, wait for port, then test:
import subprocess, time, requests
from playwright.sync_api import sync_playwright

proc = subprocess.Popen(["pnpm", "dev"])
# Wait for server ready
for _ in range(30):
    try:
        requests.get("http://localhost:3000", timeout=1)
        break
    except:
        time.sleep(1)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:3000")
    page.wait_for_load_state("networkidle")  # CRITICAL: wait for JS
    # ... test logic
    browser.close()

proc.terminate()
```

## Common Patterns

### Screenshot for debugging
```python
page.screenshot(path="debug.png", full_page=True)
```

### Find elements after JS renders
```python
page.wait_for_load_state("networkidle")
page.wait_for_selector(".my-component", timeout=5000)
element = page.locator(".my-component")
```

### Check for console errors
```python
errors = []
page.on("console", lambda msg: errors.append(msg) if msg.type == "error" else None)
page.goto(url)
page.wait_for_load_state("networkidle")
if errors:
    print("Console errors:", [e.text for e in errors])
```

### Form interaction
```python
page.fill('input[name="email"]', "test@example.com")
page.fill('input[name="password"]', "secret")
page.click('button[type="submit"]')
page.wait_for_url("**/dashboard")
```

## Verification After Testing

Use `verification-before-completion` before claiming tests pass. Show actual Playwright output, not "should work".

## Install (if needed)
```bash
pip install playwright
playwright install chromium
```
