"""Rebuild this self-authored fixture only; not a general PDF-to-lesson converter.

Requires Python 3, reportlab, and pdftoppm on PATH. No network calls.
"""

import hashlib
import html
import shutil
import subprocess
from pathlib import Path

from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1] / "skills" / "personalized-courseware"
ARRAY = [1, 3, 5, 7, 9, 11, 13]
TARGETS = [1, 7, 13, 8]


def make_source():
	path = HERE / "source.pdf"
	c = canvas.Canvas(str(path), pagesize=(720, 540), invariant=1)
	c.setTitle("Binary search: interval, invariant, algorithm")
	c.setAuthor("yoooteacher self-authored example")
	def page(title, printed):
		c.setFillColorRGB(.08, .15, .2)
		c.setFont("Helvetica-Bold", 27)
		c.drawString(42, 490, title)
		c.setFont("Helvetica", 12)
		c.drawString(42, 22, f"Self-authored teaching fixture | Slide {printed}")
	def lines(items, y=430, font="Helvetica", size=19, step=34):
		c.setFont(font, size)
		for line in items:
			c.drawString(42, y, line)
			y -= step
	page("1. Sorted input and candidate interval", 4)
	lines([
		"Precondition: a is a finite nondecreasing array.",
		"For valid indices i < j, a[i] <= a[j].",
		"Goal: return any index of x, or -1 if x is absent.",
		"Candidate interval: [l, r], with both endpoints included.",
	])
	for i, value in enumerate(ARRAY):
		x = 48 + i * 88
		c.rect(x, 175, 80, 62)
		c.setFont("Helvetica-Bold", 22)
		c.drawCentredString(x + 40, 198, str(value))
		c.setFont("Helvetica", 16)
		c.drawCentredString(x + 40, 150, f"i={i}")
	lines(["Example: x = 11; initially l = 0, r = 6.", "The boxes show values; i labels zero-based indices."], y=100, size=18, step=30)
	c.showPage()
	page("2. Why discarding half is safe", 5)
	lines([
		"Invariant: if x occurs, an occurrence remains in [l, r].",
		"Initially: [0, n - 1] contains every valid index.",
		"Choose m = floor((l + r) / 2).",
		"If a[m] < x: for i <= m, a[i] <= a[m] < x.",
		"Therefore set l = m + 1. No occurrence is discarded.",
		"If a[m] > x: symmetrically set r = m - 1.",
		"If a[m] = x: return m.",
		"Each unequal step strictly shrinks the interval.",
		"When l > r, no candidate remains; return -1.",
	], size=18, step=38)
	c.showPage()
	page("3. Algorithm and worked trace", 6)
	code = [
		"l, r = 0, len(a) - 1",
		"while l <= r:",
		"    m = (l + r) // 2",
		"    if a[m] == x:",
		"        return m",
		"    if a[m] < x:",
		"        l = m + 1",
		"    else:",
		"        r = m - 1",
		"return -1",
	]
	# Spaces here are literal source-slide text; Python implementation uses tabs.
	lines(code, y=430, font="Courier", size=18, step=27)
	lines([
		"x = 11: [0, 6] -> m = 3, a[m] = 7 -> l = 4",
		"         [4, 6] -> m = 5, a[m] = 11 -> return 5",
		"Empty input returns -1. Duplicates: any match is valid.",
	], y=125, size=17, step=30)
	c.save()
	return path


def trace(target):
	l, r = 0, len(ARRAY) - 1
	rows = []
	while l <= r:
		m = (l + r) // 2
		if ARRAY[m] == target:
			rows.append((l, r, m, ARRAY[m], f"命中，返回 {m}"))
			return rows
		if ARRAY[m] < target:
			action = f"左端移到 {m + 1}"
			rows.append((l, r, m, ARRAY[m], action))
			l = m + 1
		else:
			action = f"右端移到 {m - 1}"
			rows.append((l, r, m, ARRAY[m], action))
			r = m - 1
	rows.append((l, r, "—", "—", "区间为空，返回 −1"))
	return rows


def state_table(target):
	rows = "".join(f"<tr><td>[{l}, {r}]</td><td>{m}</td><td>{value}</td><td>{action}</td></tr>" for l, r, m, value, action in trace(target))
	return f'<h3>目标 x = {target}</h3><table class="trace-table"><caption>x = {target} 的完整静态状态</caption><thead><tr><th scope="col">候选区间</th><th scope="col">m</th><th scope="col">a[m]</th><th scope="col">理由与更新</th></tr></thead><tbody>{rows}</tbody></table>'


def source_figure(page, caption):
	return f'<figure><div class="original-page" tabindex="0" role="region" aria-label="原课件第 {page} 页，窄屏可横向滚动"><a href="source-{page}.png"><img src="source-{page}.png" alt="自制原课件第 {page} 页：{caption}；完整转录和解释见紧邻正文。" width="1200" height="900"></a></div><figcaption>原图 · 未裁切的原课件整页；窄屏可横向滚动，点击放大。<a href="source.pdf#page={page}">source.pdf · PDF 第 {page} 页 · Slide {page + 3}</a>。{caption}</figcaption></figure>'


def lesson(level):
	novice = level == "foundation"
	title = "展开基础与证明" if novice else "简短回顾与条件核对"
	start = "有序性的含义还不清楚；闭区间见过但不会稳定更新。本版补充排除依据，并展开不变量的建立、保持和终止。" if novice else "已有回答能解释有序性、区间排除和循环不变量。本版保留原证明，只简短提醒基础，重点核对终止与重复值语义。"
	intro = """<aside class="supplement"><h3>新增前置解释 · 有序性让排除成为可能</h3><p>非降序允许相等，只要求越靠右不更小。例如原图里索引 3 的值是 7；它左边的值都不超过 7。找 11 时，这些位置都不可能命中，所以一次能排除多个位置。若数组未排序，左侧可能藏着 11，这一步就不成立。</p><p>索引是位置，从 0 开始；值是格子里的数。[0, 6] 包含两端，共 6 − 0 + 1 = 7 个位置。返回 5 表示第六个位置，不是说目标值等于 5。</p><p>回到原课件 Slide 4：我们现在有理由把“寻找一个值”变成“维护仍可能含有答案的区间”。</p></aside>""" if novice else """<p class="supplement">辅助解释 · 非降序允许重复值；[l, r] 是闭区间。有序性将一次比较变成对整段候选位置的排除。沿原课件进入安全性证明。</p>"""
	proof = """<aside class="supplement"><h3>新增解释 · 不变量不是“数组不变化”</h3><p>不变量是每轮开始都仍然成立的一句话：如果答案存在，候选区间里至少还保留一个答案。它连接了“缩小区间”和“不会漏答案”这两个目标。</p><ol><li><strong>建立：</strong>初始区间覆盖所有位置，所以任何存在的答案都在其中。空数组时区间是 [0, −1]，没有有效位置，也不会进入循环。</li><li><strong>保持（向右找）：</strong>若 a[m] &lt; x，左侧任何位置 i 的值满足 a[i] ≤ a[m] &lt; x，左侧连同中点都不等于目标。排除它们后，存在的答案仍在 [m + 1, r]。</li><li><strong>保持（向左找）：</strong>若 a[m] &gt; x，右侧任何 i ≥ m 满足 a[i] ≥ a[m] &gt; x，所以保留 [l, m − 1]。等于目标时直接返回中点。</li></ol><p><strong>进度提醒：</strong>现在已说明每步不会漏答案，还需要说明循环会停，以及停下时的结果可信。</p><ol start="4"><li><strong>终止：</strong>非空区间长度是 r − l + 1。向右更新后长度变为 r − m，向左更新后变为 m − l，都比旧长度小；长度不能无限下降而仍为正。</li><li><strong>回到目标：</strong>找到时返回的位置确实有 x。若区间变空但 x 存在，就与不变量矛盾，所以此时可以返回 −1。这完成了 Slide 4 提出的任务。</li></ol></aside>""" if novice else """<div class="supplement"><p>辅助解释 · 原证明的右侧排除同理来自 i ≥ m ⇒ a[i] ≥ a[m] &gt; x。初始化覆盖全域，保持依赖非降序性；相等时返回有效索引。</p><p>终止度量取非空区间长度 r − l + 1。更新后分别为 r − m 或 m − l，严格减少。空区间与“存在答案仍在区间内”的不变量合起来推出不存在答案。这样回到 Slide 4 的返回值契约。</p></div>"""
	code = "l, r = 0, len(a) - 1\nwhile l <= r:\n\tm = (l + r) // 2\n\tif a[m] == x:\n\t\treturn m\n\tif a[m] < x:\n\t\tl = m + 1\n\telse:\n\t\tr = m - 1\nreturn -1"
	static = "".join(state_table(x) for x in TARGETS)
	body = f'''<header>
	<p class="eyebrow">自制公开候选示例 · 人工模拟学生配置</p>
	<h1>二分查找：从候选区间到正确算法</h1>
	<p>{title}。本章问题：在有序数组中找到目标，并说明每次排除为什么安全。</p>
	<p><strong>暂定学习起点：</strong>{start}这是预设回答的演示，不是真实学生测评；可修改 learner-profiles.md 中的知识点证据。</p>
	<div class="controls" hidden><label for="font-size">字号</label><select id="font-size"><option value="18">标准</option><option value="21">较大</option><option value="24">大</option></select><button id="print" type="button">打印 / 保存为 PDF</button></div>
	<nav aria-label="本章目录"><a href="#concept">1 概念</a><a href="#proof">2 证明</a><a href="#algorithm">3 算法</a></nav>
</header>
<section id="concept"><h2>1. 有序输入与候选区间</h2>
{source_figure(1, "有序数组、任务目标与索引图。")}
<blockquote lang="en">Precondition: a is a finite nondecreasing array.<br>For valid indices i &lt; j, a[i] &lt;= a[j].<br>Goal: return any index of x, or -1 if x is absent.<br>Candidate interval: [l, r], with both endpoints included.<span class="source">原文逐字引用 · source.pdf · PDF 第 1 页 · Slide 4</span></blockquote>
<p>翻译 · 前提：a 是有限的非降序数组。对有效索引 i &lt; j，有 a[i] ≤ a[j]。目标是返回 x 的任意一个索引；不存在时返回 −1。候选区间 [l, r] 包含两端。</p>
<p>原例翻译 · x = 11，初始 l = 0、r = 6。方框内为值，下方 i 表示从 0 开始的索引。来源同上。</p>
{intro}
</section>
<section id="proof"><h2>2. 为什么排除一半是安全的</h2>
<p>辅助衔接 · 上一节确定了要维护的区间；现在证明缩小它不会丢掉答案，再说明过程能够结束。</p>
{source_figure(2, "不变量、排除依据与终止条件。")}
<blockquote lang="en">Invariant: if x occurs, an occurrence remains in [l, r].<span class="source">原文逐字引用 · source.pdf · PDF 第 2 页 · Slide 5</span></blockquote>
<p>翻译 · 不变量：如果 x 出现，区间 [l, r] 中仍保留至少一个出现位置。</p>
<ol><li>翻译 · 初始 [0, n − 1] 包含所有有效索引。</li><li>翻译 · 选择 <span class="math">m = ⌊(l + r) / 2⌋</span>。</li><li>翻译 · 若 a[m] &lt; x，对 i ≤ m 有 a[i] ≤ a[m] &lt; x，因此令 l = m + 1；没有丢掉任何目标位置。</li><li>翻译 · 若 a[m] &gt; x，对称地令 r = m − 1。</li><li>翻译 · 若 a[m] = x，返回 m。</li><li>翻译 · 每个不相等的步骤都严格缩小区间；当 l &gt; r 时无候选，返回 −1。</li></ol>
<p class="source">以上步骤按原顺序翻译 · source.pdf · PDF 第 2 页 · Slide 5；不等式沿原符号。</p>
{proof}
</section>
<section id="algorithm"><h2>3. 算法与完整例题</h2>
<p>辅助衔接 · 安全性与终止已得到解释，接下来按原课件将这些结论落实到边界更新，并跟踪同一个例子。</p>
{source_figure(3, "算法伪代码与 x = 11 的两步轨迹。")}
<pre><code>{html.escape(code)}</code></pre>
<p class="source">原代码转录 · source.pdf · PDF 第 3 页 · Slide 6；仅缩进改为 Tab。它是函数体片段，输入前提见第 1 节。</p>
<p>原例翻译 · x = 11：先在 [0, 6] 取 m = 3，a[m] = 7，所以 l = 4；再在 [4, 6] 取 m = 5，a[m] = 11，返回 5。空输入返回 −1；有重复值时，返回任意命中位置即可。来源：source.pdf · PDF 第 3 页 · Slide 6。</p>
<p class="supplement">新增解题解释 · 此例选择二分查找的依据是输入非降序；每一步利用已证的排除规则。返回 5 对应 a[5] = 11。原文没有要求第一个重复值，不能把这一算法当作查找首个位置的算法。</p>
<h3>辅助交互 · 换一个目标，哪段仍是候选？</h3>
<p>固定使用原图数组 [1, 3, 5, 7, 9, 11, 13]。手动选择目标与步骤，不自动播放。下方始终保留所有可选目标的完整静态轨迹。</p>
<div class="controls" id="trace-controls" hidden><label for="target">目标</label><select id="target"><option>1</option><option>7</option><option>13</option><option>8</option></select><button type="button" id="previous">上一步</button><button type="button" id="next">下一步</button></div>
<p id="live-state" class="interactive-state" aria-live="polite"></p>
<div id="static-states">{static}</div>
<p class="source">新增辅助演示 · 使用 Slide 4 的数组和 Slide 6 的规则；1、7、13、8 是补充例子。表内区间为每步比较之前的状态，空区间行不读取数组。</p>
<p>回到本章目标：有序性允许整段排除，不变量保证答案不丢失，严格缩小保证结束，最终返回一个正确索引或 −1。本次未提供其他章节，不添加跨章节引用。</p>
</section>'''
	skeleton = (SKILL / "assets" / "lesson.html").read_text()
	start_at = skeleton.index('\t\t<header>')
	end_at = skeleton.index('\n\t</main>')
	output = skeleton[:start_at] + body + skeleton[end_at:]
	output = output.replace("课件标题 · 个性化学习材料", f"二分查找 · {title}")
	output = output.replace("</body>", '\t<script src="lesson.js"></script>\n</body>')
	(HERE / f"{level}.html").write_text(output)


def main():
	if not shutil.which("pdftoppm"):
		raise SystemExit("Missing pdftoppm: install Poppler or use the checked-in example files.")
	path = make_source()
	render = subprocess.run(["pdftoppm", "-scale-to", "1200", "-png", str(path), str(HERE / "source")], capture_output=True, text=True)
	if render.returncode:
		raise SystemExit(f"PDF rendering failed: {render.stderr[-2000:]}")
	if render.stderr:
		print(f"PDF renderer warnings (tail; inspect the images): {render.stderr[-1200:]}")
	shutil.copyfile(SKILL / "assets" / "reading.css", HERE / "reading.css")
	for level in ["foundation", "fluent"]:
		lesson(level)
	print(f"source.pdf SHA-256: {hashlib.sha256(path.read_bytes()).hexdigest()}")
	print("Built self-authored PDF, full-page original images, and two HTML examples.")


if __name__ == "__main__":
	main()
