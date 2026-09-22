## 导出 PDF 与可编辑 PPTX（可选）

deck 定稿后可一键导出两种格式（2026-07 在 35 页与 33 页两套真实 deck 上验证）：

```bash
conda activate <装有依赖的环境>
# 依赖：playwright(+chromium)、img2pdf、python-pptx；缺则 pip install img2pdf python-pptx
python3 <本 skill 目录>/scripts/export_deck.py <产出目录> --name "输出文件名"
# --pdf / --pptx 单独导出；默认两者都出，产物落在 deck 目录内
```

原理与边界，向用户交付时讲清楚：

- **PDF**：Playwright 逐页 2x 截图 + img2pdf 拼装，像素级还原（含 SVG 图表、懒加载媒体；视频页取首帧）。约 0.5MB/页
- **PPTX**：每页 = 纯视觉底图（截图时把文字设 `-webkit-text-fill-color:transparent`，保留边框卡片等 currentColor 装饰）+ 按 DOM 坐标/字号/颜色/粗体重建的**可编辑文本框**。文字均可改，但改完底图里的装饰线不会跟着动——适合「微调文字、改数字」级别的编辑，大改版式还是回 HTML 源
- 脚本自动处理：冻结入场动效、SVG 划线画满、隐藏翻页 UI、物化懒加载媒体、去掉视频 controls；旧版没有 hashchange 时需 `goto(#n)+reload()`；新版仍需等待懒加载图片与动画完成
- 文本提取的五个坑已内建处理，改脚本时别退化：① `color:transparent` + `-webkit-text-stroke` 的描边字（步骤卡编号、隔页鬼影）**留在底图**、不生成文本框——rgba 的 alpha 丢掉后会变成实心黑字压在描边上；② 伪元素文字（如 kicker 的 `::after " /"`）要读 `getComputedStyle(el,'::after').content` 才不丢；③ `letter-spacing` 映射为 OOXML `spc`（mono 标签字距是版式灵魂）；④ `white-space:nowrap` 的块（流程图节点）在 PPT 中禁止换行**并加宽文本框**（PPT 字形略宽会把末字挤出框；LibreOffice 还会无视 `wrap="none"`）；⑤ inline/块级按 computed display 判断（flex 子项与 absolute 的 span 会块化，页眉左右、角落十字才能各自成框），文本框用 content box 定位 + 非居中块以 Range 实测文字位置为起点（flex 居中的数字方块、带 padding 装饰的 li/quote 才不错位）
- 字体映射：宋体标题 → Songti SC、正文 → PingFang SC、mono → Menlo；对方机器没这些字体时 PPT 会替换，提醒用户
- **导出后 QA 必做**（文本框叠底图的错位只有渲染出来才看得见）：`soffice --headless --convert-to pdf 输出.pptx && pdftoppm -jpeg -r 100 输出.pdf qa` 出图，逐页目检；已有委派授权时可交给子代理——重点找：黑色异常大字、文字重影/压装饰（菱形、竖线、数字方块）、nowrap 节点末字溢出、页眉字距。发现问题改脚本重导，直到全绿

**PDF 太大时**（矢量导出会无损嵌入每张配图，7 张信息图能让 50 页 PDF 从 21 MB 涨到 30 MB）：用 ghostscript 只压图不动文字——`gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dDownsampleColorImages=true -dColorImageResolution=180 -dColorImageDownsampleType=/Bicubic -dAutoFilterColorImages=false -dColorImageFilter=/DCTEncode -dJPEGQ=85 -dDownsampleGrayImages=true -dGrayImageResolution=180 -dPreserveAnnots=true -sOutputFile=out.pdf in.pdf`，30 MB → 5 MB，文字仍是矢量、链接保留；另存压缩副本，不覆盖原文件；比较投影文字和链接，压完用 pypdf 核对页数与 `/Annots` 数。

