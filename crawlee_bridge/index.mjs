import express from 'express';
import { CheerioCrawler, PuppeteerCrawler, RequestQueue } from 'crawlee';
import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteerExtra.use(StealthPlugin());

const app = express();
app.use(express.json());

app.post('/scrape', async (req, res) => {
    const { url, mode } = req.body;
    
    if (!url) {
        return res.status(400).json({ error: 'URL is required' });
    }

    try {
        let resultData = null;

        const uniqueId = Date.now().toString() + Math.random().toString().slice(2, 6);
        
        if (mode === 'cheerio') {
            const rq = await RequestQueue.open(uniqueId);
            const crawler = new CheerioCrawler({
                requestQueue: rq,
                requestHandler: async ({ $, body, request }) => {
                    resultData = {
                        html: $ ? $.html() : (typeof body === 'string' ? body : JSON.stringify(body)),
                        title: $ ? $('title').text() : ''
                    };
                },
                failedRequestHandler: async ({ $, body, request }) => {
                    resultData = {
                        html: $ ? $.html() : (body ? (typeof body === 'string' ? body : JSON.stringify(body)) : ''),
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
            const crawler = new PuppeteerCrawler({
                requestQueue: rq,
                launchContext: {
                    launcher: puppeteerExtra,
                    launchOptions: {
                        headless: "new",
                        args: ['--no-sandbox', '--disable-setuid-sandbox']
                    }
                },
                requestHandler: async ({ page, request }) => {
                    // Bypass WAF by waiting a bit if there's a Turnstile challenge
                    try {
                        // wait 15 sec for cloudflare
                        await new Promise(r => setTimeout(r, 15000));
                    } catch(e) {}
                    
                    const html = await page.content();
                    const cookies = await page.cookies();
                    resultData = {
                        html,
                        cookies
                    };
                },
                failedRequestHandler: async ({ page, request }) => {
                    if (page) {
                        try {
                            const html = await page.content();
                            const cookies = await page.cookies();
                            resultData = { html, cookies };
                        } catch(e) {}
                    }
                },
                maxRequestRetries: 0,
                maxRequestsPerCrawl: 1,
                requestHandlerTimeoutSecs: 30,

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
