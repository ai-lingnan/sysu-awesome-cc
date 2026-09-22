# 组件目录：页型、内容预算与自绘图

模板 `assets/template.html` 里每种页型都有一页可运行的示例，本文档讲**怎么选、怎么填、填多少**。这些内容预算以 1280×720 舞台为起点，仍需用实际内容截图检查溢出。

## 页型速查

| 页型 | class | 用在什么时候 | 内容预算 |
|:--|:--|:--|:--|
| 封面 | `s-title` | 第 1 页 | 主标题一行 ≤ 13 个汉字（78px），更长时断两行或降到 64px；系列课单讲的副标题写“课程名 · Week N” |
| 章节隔页 | `s-div` + `data-dark` | 每个 Part 开头；第一张兼作总目录 | 左侧部分名 ≤ 2 行、落点 ≤ 2 行；右侧 `.plist.divlist` 列全部 Part（≤ 7 项，放大的当前项也要一行放下）；ghost 用罗马数字（mono 描边）。转场与规则见[封面与目录](cover-and-navigation.md) |
| 编辑部列表 | `.ed` / `.ed.tight` | 最常用正文页 | `.ed` 3–4 条、`.ed.tight` 4–5 条；每条 ≤ 1.5 行 |
| 楷体引文 | `.quote` | 列表页收尾金句 | 一句话；页内至多一处 |
| 双栏对比 | `.duo` | 旧 vs 新、差 vs 好 | 每栏 3–4 条短句，两栏条数对齐 |
| 表格 | `table` | 结构化信息 | 3–5 行 × 3–4 列；单元格 ≤ 1 行半；6 行用 `table.dense`（紧凑变体，已含于模板） |
| 步骤卡 | `.steps` | 流程、演示环节 | 2–4 张卡；卡内标题 ≤ 5 字 + 正文 2 行；卡内用 `<br>` 手动控行成整齐两行，防词语拆行/单字悬挂 |
| 阶段路线 | `.road` | 演进、里程碑 | 3–5 列；列标题 ≤ 6 字，每列 2–3 条短语 |
| 图文行 | `.row` | 左文右图 | 左侧 2–4 条、右侧 `.fig` 放图 |
| 主体信息图 | `s-fig` + `.figbox > img.figimg` | 图承担主体讲解 | 标题 + 一张 21:9 图（约 410px 高）+ 一句落点；图用 `data-src` 懒加载。标记示例在模板注释里，配色与生成见[图像交付指南](gpt-image-infographics.md) |
| 文件树 | `.tree` | 目录结构、索引/代码样例 | mono 白底块，`white-space:pre` 手动排行，≤ 8 行；重点行用 b 标红（已含于模板） |
| 金句页 | `s-key` | 核心观点，全场 1–3 页 | 大字 ≤ 2 行，`em` 标红关键短语 |
| 流程图 | `.flow` | 输入→处理→输出 | 两侧各 2–4 个节点，中枢 1 个 |
| 尾页 | `s-end` | 最后一页 | 谢谢 + 主讲人信息 |

超预算时优先调整布局、断行、拆页或删去重复文字，保持投影可读字号；保留用户已确认的含义。

正文默认字号已按 2026-07 真实课堂反馈整体调大一档（列表 23px、表格 21px、步骤卡 19px 等，标题不变）——投影场景下再小观众看不清。因此内容预算按上表执行，不要为塞更多字回调字号。

2026-08 再次验证同一方向：一批实操步骤页因为用了最小字号档（xs 列表 17.5px、行内 16.5px 侧栏），被用户连续两次要求「正文整体放大一号」，最终整体 +3px（xs 列表 20.5px、表格 19.5px、指令块 18px）且七页无一溢出——说明这批页面有放大正文的空间。规则：小字号档（xs/mini）只给真挤不下的页面；截图审阅时看到页面下方有整块留白，就该把正文放大一档填上去。标题一行放不下时，优先合理断行与调整布局，保留用户已确认的措辞；缩短时不能改变含义，不靠缩小 h1 字号硬塞。

## 通用结构（正文页）

```html
<section class="slide" data-k="第一部分 · 章节名">
  <div class="kicker" data-a><span class="n">I</span>小节名</div>
  <h1 data-a>页标题，可用 <em>标红</em></h1>
  <div class="rule" data-a></div>
  <!-- 内容组件 -->
</section>
```

- `data-a` = 参与交错入场。所有可见块都该加，JS 按文档序自动分配延迟
- `data-k` 决定页脚章节名和进度条气泡文字，同章各页保持一致
- kicker 的 `.n` 用罗马数字（I II III IV）对应章节序，CSS 自动补 " /" 分隔

## 精确或可编辑图的三种自绘模式

下面适用于需要精确线条、数值或可编辑标签的图。GPT Image 主体信息图采用外置图片，可跨整行；按 [图像交付指南](gpt-image-infographics.md) 生成与装页。

### 1. SVG 划线图表（趋势、对比曲线）

```html
<div class="chartwrap" data-a>
  <svg width="760" height="300" viewBox="0 0 760 300" fill="none">
    <!-- 坐标轴（细线灰） -->
    <line x1="60" y1="20" x2="60" y2="252" stroke="#D8CFC2" stroke-width="1.5"/>
    <line x1="60" y1="252" x2="720" y2="252" stroke="#D8CFC2" stroke-width="1.5"/>
    <!-- 图例放左上角（不要标在曲线旁——会压线） -->
    <line x1="96" y1="30" x2="136" y2="30" stroke="var(--brand)" stroke-width="4"/>
    <text x="148" y="36" font-size="17" fill="#A5171C" font-weight="700">主曲线含义</text>
    <!-- 曲线：class="ln" + pathLength="1" 触发划线动画；第二条加 d2 错峰 -->
    <path class="ln" d="M 80 225 C 280 215, 460 130, 690 55"
          stroke="#A5171C" stroke-width="4" pathLength="1"/>
    <circle cx="690" cy="55" r="6" fill="#A5171C"/>
  </svg>
</div>
```

要点：主线用品牌色粗线（4px），对照线用灰虚线（2.5px + `stroke-dasharray="7 7"`）；端点加实心圆；文字标签一律放图例区，别沿曲线摆。

### 2. 流程图 `.flow`（见模板第 10 页）

输入组 → 箭头 → 中枢（品牌色实底）→ 箭头 → 输出组。输出节点加 `.out`（左红边），特殊通道加 `.push`（红虚线框）。节点文字 ≤ 12 字。

### 3. 中枢辐射图 `.hub`（一个核心多个卫星）

```html
<div class="hub" data-a>
  <svg viewBox="0 0 380 330">
    <line x1="190" y1="165" x2="80"  y2="40"/>
    <line x1="190" y1="165" x2="300" y2="40"/>
    <line x1="190" y1="165" x2="60"  y2="285"/>
    <line x1="190" y1="165" x2="320" y2="285"/>
  </svg>
  <div class="c"><b>中心节点</b><span>小注</span></div>
  <div class="nd" style="left:22px;top:22px;">卫星一</div>
  <div class="nd" style="right:14px;top:22px;">卫星二</div>
  <div class="nd" style="left:6px;bottom:22px;">卫星三</div>
  <div class="nd" style="right:6px;bottom:22px;">卫星四</div>
</div>
```

需配 `.hub` 样式（模板未含时补进 CSS）：

```css
.hub{position:relative;width:380px;height:330px;}
.hub .c{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  background:var(--brand);color:#fff;padding:20px 26px;text-align:center;z-index:2;}
.hub .c b{font-family:var(--serif);font-size:21px;display:block;}
.hub .c span{font-size:12px;letter-spacing:.15em;opacity:.85;}
.hub .nd{position:absolute;border:1px solid var(--hair);background:#fff;
  padding:9px 16px;font-size:15px;color:var(--ink2);white-space:nowrap;z-index:2;}
.hub svg{position:absolute;inset:0;z-index:1;}
.hub svg line{stroke:#D8C9BF;stroke-width:1.5;}
```

### 4. 大字部件 `.organ`（汉字做视觉锚点）

右栏三行左右，每行一个宋体大字 + 标签 + 小注（见模板第 8 页）。适合"三要素""三支柱"类概念——比图标更有中文版式的味道。

## 结构变体：三层结构图 `.layers`

平级堆叠的层级示意（补进 CSS 后用）：

```css
.layers{width:520px;}
.layers .ly{border:1px solid var(--hair);background:#fff;padding:16px 24px;
  display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;}
.layers .ly b{font-family:var(--serif);font-size:21px;font-weight:900;}
.layers .ly span{font-size:14px;color:var(--sub);letter-spacing:.1em;}
.layers .ly.mid{border:1.5px dashed #C99490;}
.layers .ly.mid b,.layers .ly.mid span{color:var(--brand);}
```

注意：多层并列时**不要单独放大某一层**——除非那页的论点就是"这层出了问题"，即便如此也只用虚线边示意，尺寸字号保持平权（这是真实用户反馈）。

## 强调的经济学

红色是稀缺资源：每页 `b` 标红 ≤ 3 处、`em`/quote 金句 ≤ 1 处、表格不高亮整行（除非论点就在那行）。宁可少，不可滥——观众的眼睛跟着红色走，红多了等于没有红。
