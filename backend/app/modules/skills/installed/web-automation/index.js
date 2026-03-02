#!/usr/bin/env node

/**
 * 网页自动化技能
 * 
 * 支持功能：
 * - scrape: 抓取网页内容
 * - screenshot: 网页截图
 * - fill_form: 填写表单
 * - click: 点击元素
 * - navigate: 页面导航
 */

const puppeteer = require('puppeteer');
const cheerio = require('cheerio');

// 解析命令行参数
function parseArgs() {
    const args = process.argv.slice(2);
    const params = {};
    
    for (let i = 0; i < args.length; i += 2) {
        if (args[i] === '--params' && args[i + 1]) {
            try {
                return JSON.parse(args[i + 1]);
            } catch (e) {
                console.error('参数解析失败:', e.message);
                process.exit(1);
            }
        }
    }
    
    return params;
}

// 抓取网页内容
async function scrapePage(page, selector) {
    const content = await page.content();
    const $ = cheerio.load(content);
    
    if (selector) {
        const elements = $(selector);
        const results = [];
        
        elements.each((index, element) => {
            results.push({
                text: $(element).text().trim(),
                html: $(element).html(),
                attributes: element.attribs
            });
        });
        
        return {
            count: results.length,
            data: results
        };
    } else {
        // 提取页面基本信息
        const title = $('title').text();
        const description = $('meta[name="description"]').attr('content') || '';
        const headings = [];
        
        $('h1, h2, h3').each((index, element) => {
            headings.push({
                level: element.tagName,
                text: $(element).text().trim()
            });
        });
        
        const links = [];
        $('a[href]').each((index, element) => {
            links.push({
                text: $(element).text().trim(),
                href: $(element).attr('href')
            });
        });
        
        return {
            title,
            description,
            headings: headings.slice(0, 10),
            links: links.slice(0, 20),
            text: $('body').text().trim().substring(0, 5000)
        };
    }
}

// 网页截图
async function takeScreenshot(page, options = {}) {
    const screenshotOptions = {
        type: options.type || 'png',
        fullPage: options.fullPage !== false
    };
    
    if (options.selector) {
        const element = await page.$(options.selector);
        if (element) {
            return await element.screenshot(screenshotOptions);
        }
    }
    
    return await page.screenshot(screenshotOptions);
}

// 填写表单
async function fillForm(page, formData) {
    const results = [];
    
    for (const [selector, value] of Object.entries(formData)) {
        try {
            await page.waitForSelector(selector, { timeout: 5000 });
            
            const element = await page.$(selector);
            const tagName = await element.evaluate(el => el.tagName.toLowerCase());
            
            if (tagName === 'input') {
                const inputType = await element.evaluate(el => el.type);
                
                if (inputType === 'checkbox' || inputType === 'radio') {
                    if (value) {
                        await element.click();
                    }
                } else {
                    await element.type(String(value));
                }
            } else if (tagName === 'textarea') {
                await element.type(String(value));
            } else if (tagName === 'select') {
                await element.select(String(value));
            }
            
            results.push({ selector, success: true });
        } catch (error) {
            results.push({ selector, success: false, error: error.message });
        }
    }
    
    return {
        filled: results.filter(r => r.success).length,
        failed: results.filter(r => !r.success).length,
        details: results
    };
}

// 点击元素
async function clickElement(page, selector) {
    try {
        await page.waitForSelector(selector, { timeout: 5000 });
        await page.click(selector);
        
        return {
            success: true,
            selector,
            message: '元素点击成功'
        };
    } catch (error) {
        return {
            success: false,
            selector,
            error: error.message
        };
    }
}

// 主函数
async function main() {
    const params = parseArgs();
    
    const {
        action,
        url,
        selector,
        formData,
        waitFor,
        viewport = { width: 1280, height: 720 }
    } = params;
    
    if (!action || !url) {
        console.error(JSON.stringify({
            success: false,
            error: '缺少必要参数: action 和 url'
        }));
        process.exit(1);
    }
    
    let browser;
    
    try {
        // 启动浏览器
        browser = await puppeteer.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        const page = await browser.newPage();
        
        // 设置视口
        await page.setViewport(viewport);
        
        // 导航到页面
        await page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        // 等待特定元素
        if (waitFor) {
            await page.waitForSelector(waitFor, { timeout: 10000 });
        }
        
        let result;
        
        // 执行操作
        switch (action) {
            case 'scrape':
                result = await scrapePage(page, selector);
                break;
                
            case 'screenshot':
                const screenshot = await takeScreenshot(page, { selector, ...params });
                result = {
                    screenshot: screenshot.toString('base64'),
                    format: params.type || 'png'
                };
                break;
                
            case 'fill_form':
                if (!formData) {
                    throw new Error('fill_form 操作需要提供 formData 参数');
                }
                result = await fillForm(page, formData);
                break;
                
            case 'click':
                if (!selector) {
                    throw new Error('click 操作需要提供 selector 参数');
                }
                result = await clickElement(page, selector);
                break;
                
            case 'navigate':
                result = {
                    success: true,
                    url: page.url(),
                    title: await page.title()
                };
                break;
                
            default:
                throw new Error(`不支持的操作: ${action}`);
        }
        
        // 输出结果
        console.log(JSON.stringify({
            success: true,
            action,
            url,
            result
        }, null, 2));
        
    } catch (error) {
        console.error(JSON.stringify({
            success: false,
            error: error.message,
            stack: error.stack
        }));
        process.exit(1);
        
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// 运行主函数
main();
