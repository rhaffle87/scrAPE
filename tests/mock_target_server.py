from fastapi import FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
import json

app = FastAPI(title="E2E Mock Target Server for scrAPE")

@app.get("/status/{status_code}")
async def get_status(status_code: int):
    """Simulates generic HTTP limits (e.g. 403 Forbidden, 429 Too Many Requests)."""
    return Response(status_code=status_code, content=f"Returned {status_code}")

@app.get("/js_challenge", response_class=HTMLResponse)
async def get_js_challenge():
    """Returns a static HTML page that executes JavaScript to load the target payload after a delay."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JS Challenge</title>
    </head>
    <body>
        <h1>Please wait... Checking your browser.</h1>
        <div id="target-container"></div>
        <script>
            setTimeout(() => {
                document.getElementById('target-container').innerHTML = '<div class="stealth-payload" data-secret="bypass-success">Target Content Loaded via JS!</div>';
            }, 500); // 500ms delay to make tests fast but still require JS evaluation
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/waf_escalation")
async def get_waf_escalation(request: Request):
    """
    A stateful endpoint that tracks client IP/Sessions or cookies.
    It returns 403 unless a specific 'trusted' stealth cookie is passed,
    or the User-Agent indicates a stealth browser.
    For simplicity in E2E, we'll check for a custom header or cookie that
    only the advanced fallback tiers inject, or we'll just check if it's headless.
    Actually, to test fallback: we return 403 if it looks like standard httpx.
    """
    user_agent = request.headers.get("user-agent", "").lower()
    
    # If it's the default httpx user-agent, block it.
    if "python-httpx" in user_agent:
        return Response(status_code=status.HTTP_403_FORBIDDEN, content="Blocked by WAF")
        
    # To truly simulate a WAF that requires JS evaluation, we could return a 403
    # unless a cookie "waf_passed=true" is present. For now, returning 200 for
    # non-httpx user agents proves escalation occurred.
    return {"status": "success", "message": "WAF bypassed successfully"}

@app.get("/heavy-spa-data")
async def get_heavy_spa_data():
    """Data payload for the heavy SPA."""
    import asyncio
    await asyncio.sleep(1) # Simulate slow network API
    return {"media_url": "https://example.com/dynamic-media.mp4", "alt_text": "Dynamic Video Content"}

@app.get("/heavy-spa", response_class=HTMLResponse)
async def get_heavy_spa():
    """Simulates a heavy React/Vue SPA that requires 2-5s to hydrate and load data."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Heavy SPA Simulation</title>
    </head>
    <body>
        <div id="root">Loading App Shell...</div>
        <script>
            // Simulate 500ms React hydration delay
            setTimeout(() => {
                document.getElementById('root').innerHTML = '<h2>Hydrated. Fetching Data...</h2><div id="media-container"></div>';
                
                // Fetch dynamic API data
                fetch('/heavy-spa-data')
                    .then(response => response.json())
                    .then(data => {
                        // Simulate additional processing time
                        setTimeout(() => {
                            document.getElementById('media-container').innerHTML = 
                                `<video src="${data.media_url}" class="lazy-video" alt="${data.alt_text}"></video>`;
                        }, 200);
                    });
            }, 500);
        </script>
    </body>
    </html>
    """
    return html_content
