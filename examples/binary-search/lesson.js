// Self-authored demonstration; data and targets are local and bounded.
function binaryTrace(a, x) {
	if (!Array.isArray(a) || !Number.isFinite(x) || a.some((v, i) => !Number.isFinite(v) || (i > 0 && v < a[i - 1]))) {
		throw new TypeError('Expected a finite nondecreasing numeric array and finite target.');
	}
	const steps = [];
	let l = 0;
	let r = a.length - 1;
	while (l <= r) {
		const m = Math.floor((l + r) / 2);
		const value = a[m];
		const action = value === x ? `命中，返回 ${m}` : value < x ? `左端移到 ${m + 1}` : `右端移到 ${m - 1}`;
		steps.push({ l, r, m, value, action });
		if (value === x) return { steps, result: m };
		if (value < x) l = m + 1;
		else r = m - 1;
	}
	steps.push({ l, r, m: null, value: null, action: '区间为空，返回 −1' });
	return { steps, result: -1 };
}

if (typeof module !== 'undefined') module.exports = { binaryTrace };

if (typeof document !== 'undefined') {
	const target = document.querySelector('#target');
	const previous = document.querySelector('#previous');
	const next = document.querySelector('#next');
	const state = document.querySelector('#live-state');
	let current = 0;
	function render() {
		const { steps } = binaryTrace([1, 3, 5, 7, 9, 11, 13], Number(target.value));
		const step = steps[current];
		state.textContent = `第 ${current + 1} / ${steps.length} 步：候选区间 [${step.l}, ${step.r}]；${step.m === null ? '无有效中点' : `m = ${step.m}，a[m] = ${step.value}`}；${step.action}。`;
		previous.disabled = current === 0;
		next.disabled = current === steps.length - 1;
	}
	target.addEventListener('change', () => { current = 0; render(); });
	previous.addEventListener('click', () => { current--; render(); });
	next.addEventListener('click', () => { current++; render(); });
	document.querySelector('#trace-controls').hidden = false;
	render();
}
