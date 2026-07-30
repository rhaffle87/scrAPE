import express from 'express';
import crypto from 'node:crypto';
import { CheerioCrawler, PuppeteerCrawler, RequestQueue, ProxyConfiguration } from 'crawlee';
import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteerExtra.use(StealthPlugin());
const app = express();
app.disable('x-powered-by');
app.use(express.json());

app.get('/', (req, res) => {
    res.json({ status: 'ok', service: 'crawlee_bridge' });
});

app.post('/scrape', async (req, res) => {
    const { url, mode, proxy, userDataDir } = req.body;

    if (!url) {
        return res.status(400).json({ error: 'URL is required' });
    }

    try {
        let resultData = null;
        let proxyConfiguration;

        if (proxy) {
            proxyConfiguration = new ProxyConfiguration({ proxyUrls: [proxy] });
        }

        const uniqueId = Date.now().toString() + crypto.randomBytes(4).toString('hex');

        if (mode === 'cheerio') {
            const rq = await RequestQueue.open(uniqueId);
            const crawler = new CheerioCrawler({
                proxyConfiguration,
                requestQueue: rq,
                requestHandler: async ({ $, body, request }) => {
                    let htmlContent = '';
                    if ($) {
                        htmlContent = $.html();
                    } else if (typeof body === 'string') {
                        htmlContent = body;
                    } else {
                        htmlContent = JSON.stringify(body);
                    }
                    resultData = {
                        html: htmlContent,
                        title: $ ? $('title').text() : ''
                    };
                },
                failedRequestHandler: async ({ $, body, request }) => {
                    let htmlContent = '';
                    if ($) {
                        htmlContent = $.html();
                    } else if (body && typeof body === 'string') {
                        htmlContent = body;
                    } else if (body) {
                        htmlContent = JSON.stringify(body);
                    }
                    resultData = {
                        html: htmlContent,
                        title: $ ? $('title').text() : ''
                    };
                },
                maxRequestRetries: 0,
                maxRequestsPerCrawl: 1,
            });
            await crawler.run([url]);
            await rq.drop();
        }
        else if (mode === 'puppeteer') {
            const rq = await RequestQueue.open(uniqueId);
            
            const launchOptions = {
                headless: "new",
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            };
            if (userDataDir) {
                launchOptions.userDataDir = userDataDir;
            }

            const crawler = new PuppeteerCrawler({
                proxyConfiguration,
                requestQueue: rq,
                launchContext: {
                    launcher: puppeteerExtra,
                    launchOptions: launchOptions
                },
                requestHandler: async ({ page, request }) => {
                    // Bypass WAF by dynamically waiting for the challenge to clear
                    try {
                        let title = await page.title();
                        let content = await page.content();
                        let waitCount = 0;
                        const maxWaits = 20; // 20 * 1000ms = 20s

                        while (waitCount < maxWaits) {
                            title = title.toLowerCase();
                            content = content.toLowerCase();

                            const isChallenge =
                                title.includes("just a moment") ||
                                title.includes("attention required") ||
                                title.includes("cf-browser-verification") ||
                                content.includes("cf-turnstile") ||
                                content.includes("g-recaptcha");

                            if (!isChallenge) break;

                            await new Promise(r => setTimeout(r, 1000));
                            title = await page.title();
                            content = await page.content();
                            waitCount++;
                        }
                    } catch (e) {
                        console.error("WAF wait timeout:", e.message);
                    }

                    const html = await page.content();
                    const cookies = await page.browserContext().cookies();
                    resultData = {
                        html,
                        cookies
                    };
                },
                failedRequestHandler: async ({ page, request }) => {
                    if (page) {
                        try {
                            const html = await page.content();
                            const cookies = await page.browserContext().cookies();
                            resultData = { html, cookies };
                        } catch (e) {
                            console.error("Failed request extraction:", e.message);
                        }
                    }
                },
                maxRequestRetries: 0,
                maxRequestsPerCrawl: 1,
                requestHandlerTimeoutSecs: 60,

            });
            await crawler.run([url]);
            await rq.drop();
        } else {
            return res.status(400).json({ error: 'Invalid mode. Use cheerio or puppeteer.' });
        }

        if (resultData) {
            res.json(resultData);
        } else {
            res.status(500).json({ error: 'Failed to extract data' });
        }
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.message });
    }
});

const PORT = process.env.CRAWLEE_PORT || 10002;
app.listen(PORT, '127.0.0.1', () => {
    console.log(`Crawlee bridge running on port ${PORT}`);
});
