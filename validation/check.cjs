// Run with Node.js. Browser checks additionally need playwright and Chrome.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { binaryTrace } = require('../examples/binary-search/lesson.js');
const root = path.resolve(__dirname, '..');
const example = path.join(root, 'examples/binary-search');
const output = path.join(root, 'tmp/validation');
fs.mkdirSync(output, { recursive: true });

// Generate all nondecreasing arrays over {-1, 0, 1}, length 0..5.
const arrays = [[]];
function extend(prefix, min) {
	if (prefix.length === 5) return;
	for (let value = min; value <= 1; value++) {
		const next = [...prefix, value];
		arrays.push(next);
		extend(next, value);
	}
}
extend([], -1);
let cases = 0;
for (const a of arrays) {
	for (let x = -2; x <= 2; x++) {
		const { steps, result } = binaryTrace(a, x);
		assert.equal(result === -1, !a.includes(x));
		if (result !== -1) assert.equal(a[result], x);
		let length = a.length + 1;
		for (const step of steps) {
			assert(step.r - step.l + 1 < length);
			length = step.r - step.l + 1;
			if (a.includes(x)) assert(a.slice(step.l, step.r + 1).includes(x));
			if (step.m !== null) {
				assert(step.l <= step.m && step.m <= step.r);
				assert.equal(step.value, a[step.m]);
			}
		}
		cases++;
	}
}
for (const [a, x] of [[[2, 1], 1], [[NaN], 1], [[1], Infinity], [null, 0]]) {
	assert.throws(() => binaryTrace(a, x), TypeError);
}
assert.equal(binaryTrace([1, 3, 5, 7, 9, 11, 13], 11).result, 5);
console.log(`Algorithm: ${cases} exhaustive cases, 4 invalid inputs, original worked example passed.`);

async function browserCheck() {
	const { chromium } = require('playwright');
	const browser = await chromium.launch(process.env.CHROME_EXECUTABLE ? { executablePath: process.env.CHROME_EXECUTABLE } : { channel: 'chrome' });
	const results = [];
	try {
		for (const level of ['foundation', 'fluent']) {
			const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
			const page = await context.newPage();
			const errors = [];
			page.on('pageerror', error => errors.push(String(error)));
			await page.route(/^https?:/, route => route.abort());
			await page.goto(pathToFileURL(path.join(example, `${level}.html`)).href);
			await page.evaluate(() => document.fonts.ready);
			assert.equal(await page.locator('img').count(), 3);
			assert(await page.locator('img').evaluateAll(images => images.every(img => img.complete && img.naturalWidth > 0)));
			// Compare source block order and retained file/printed page mapping.
			const sourceLinks = await page.locator('figure a[href*="source.pdf"]').evaluateAll(nodes => nodes.map(n => n.getAttribute('href')));
			assert.deepEqual(sourceLinks, [1, 2, 3].map(n => `source.pdf#page=${n}`));
			for (const node of await page.locator('[src], link[href]').evaluateAll(nodes => nodes.map(n => n.getAttribute('src') || n.getAttribute('href')))) {
				assert(!/^(https?:|\/)/.test(node), `Nonportable resource: ${node}`);
				assert(fs.existsSync(path.resolve(example, node)));
			}
			// Browser interaction must agree with permanently visible static traces.
			for (const x of [1, 7, 13, 8]) {
				await page.selectOption('#target', String(x));
				const rows = await page.locator('#static-states table').nth([1, 7, 13, 8].indexOf(x)).locator('tbody tr').evaluateAll(nodes => nodes.map(n => Array.from(n.cells, c => c.textContent)));
				for (let i = 0; i < rows.length; i++) {
					const text = await page.locator('#live-state').textContent();
					assert(text.includes(rows[i][0]) && text.includes(rows[i][3]));
					if (i < rows.length - 1) await page.click('#next');
				}
				assert(await page.locator('#next').isDisabled());
				if (rows.length > 1) {
					await page.click('#previous');
					assert((await page.locator('#live-state').textContent()).includes(rows[rows.length - 2][0]));
				}
			}
			await page.screenshot({ path: path.join(output, `${level}-desktop.png`), fullPage: true });
			const layouts = [
				{ name: 'mobile', width: 375, height: 812, font: '18' },
				{ name: 'large', width: 1280, height: 900, font: '24' },
				{ name: 'reflow-200', width: 640, height: 450, font: '24' },
			];
			for (const layout of layouts) {
				await page.setViewportSize({ width: layout.width, height: layout.height });
				await page.selectOption('#font-size', layout.font);
				assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${level} overflows in ${layout.name}`);
				if (layout.name === 'mobile') {
					// All original pixels remain accessible rather than being cropped away.
					assert(await page.locator('.original-page').first().evaluate(node => {
						node.scrollLeft = node.scrollWidth;
						const reachesEnd = Math.abs(node.scrollWidth - node.clientWidth - node.scrollLeft) <= 1;
						node.scrollLeft = 0;
						return reachesEnd;
					}));
				}
				await page.screenshot({ path: path.join(output, `${level}-${layout.name}.png`), fullPage: true });
			}
			await page.emulateMedia({ media: 'print' });
			assert(await page.locator('#trace-controls').isHidden());
			assert(await page.locator('#static-states').isVisible());
			await page.pdf({ path: path.join(output, `${level}-print.pdf`), preferCSSPageSize: true, printBackground: true });
			assert.deepEqual(errors, []);
			await context.close();
			const noJS = await browser.newContext({ javaScriptEnabled: false });
			const staticPage = await noJS.newPage();
			await staticPage.goto(pathToFileURL(path.join(example, `${level}.html`)).href);
			assert.equal(await staticPage.locator('#static-states table').count(), 4);
			assert(await staticPage.locator('.controls').first().isHidden());
			assert(await staticPage.locator('#proof').isVisible());
			await noJS.close();
			results.push({ level, sourceImages: 3, targets: 4, layouts: layouts.map(x => x.name), offline: true, noJS: true, print: true, pageErrors: errors });
		}
		fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify({ browser: await browser.version(), algorithmCases: cases, results }, null, '\t'));
		console.log('Browser: both lessons passed assets, interaction/static equivalence, reflow, no-JS, and print checks. Screenshots require human inspection.');
	} finally {
		await browser.close();
	}
}

if (process.argv.includes('--browser')) browserCheck().catch(error => { console.error(error); process.exitCode = 1; });
