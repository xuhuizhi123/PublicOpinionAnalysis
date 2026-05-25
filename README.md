# 基于 B 站评论数据的大学生就业舆情分析

按 Notebook 单元格组织的 Python 项目，新手友好。

## 项目结构

```
vibecoding1/
├── step1_crawler.py            # 爬虫：从 B 站抓评论 -> data/comments_raw.csv
├── step2_text_processing.py    # 清洗 + 分词 + 高频词 + TF-IDF
├── step3_sentiment_cluster.py  # SnowNLP 情感分析 + KMeans 主题聚类
├── step4_visualization.py      # 5 张图表（保存到 figures/）
├── step5_summary.py            # 输出文字版分析结论 -> report/summary.txt
├── requirements.txt            # 依赖
├── stopwords.txt               # 中文停用词
├── data/                       # 中间数据（运行后生成）
├── figures/                    # 图表（运行后生成）
└── report/                     # 总结文本（运行后生成）
```

## 一、安装依赖

打开 PowerShell（或 cmd），切到项目目录：

```powershell
cd E:\vibecoding1
pip install -r requirements.txt
```

如果下载慢，可以用国内镜像：

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 二、运行顺序

每个文件都是按 `# %%` 分单元格的脚本，**支持两种运行方式**：

1. **VS Code / PyCharm**：直接打开文件，每个 `# %%` 上方会出现 "Run Cell" 按钮，按顺序点击即可。
2. **Jupyter Notebook**：把 `# %%` 区块复制到对应的 Notebook 单元格里逐个运行。
3. **直接命令行**：也可以一次跑完整个脚本：

```powershell
python step1_crawler.py
python step2_text_processing.py
python step3_sentiment_cluster.py
python step4_visualization.py
python step5_summary.py
```

## 三、爬虫使用提示

### 1. 填 Cookie（建议但非必须）

打开 `step1_crawler.py`，找到：

```python
COOKIE = ""
```

把你浏览器登录 B 站后的 Cookie 整段粘进去（F12 -> Network -> 任意请求 -> Request Headers -> Cookie）。

### 2. 替换 BV 号

在 `step1_crawler.py` 的 `BV_LIST` 里，替换成你自己挑选的视频。

挑选方法：
- 在 B 站搜索 "大学生就业"、"考研还是就业"、"考公热"、"应届生找工作"、"就业难"
- 选评论较多的视频（通常 1k+ 评论的视频比较有代表性）
- 视频链接形如 `https://www.bilibili.com/video/BV1xxxxxxxxxx`，复制 `BV` 开头那一段即可

### 3. 备用方案：直接用本地 CSV

如果爬虫被风控或拿不到数据，**完全可以跳过 step1**，把已有的评论 CSV 文件改名放到：

```
data/comments_raw.csv
```

CSV 必须包含这些列（编码 utf-8-sig）：

| 列名 | 含义 |
|------|------|
| video_title | 视频标题 |
| bvid | 视频 BV 号 |
| comment | 评论内容 |
| comment_time | 评论时间（如 2024-01-01 12:00:00） |
| like_count | 点赞数 |
| reply_count | 回复数 |

然后从 step2 直接开始跑即可。

## 四、输出物清单

- `data/comments_raw.csv` —— 原始评论
- `data/comments_clean.csv` —— 清洗+分词
- `data/top_words.csv` —— 高频词 Top 50
- `data/tfidf_keywords.csv` —— TF-IDF 关键词 Top 50
- `data/comments_with_sentiment.csv` —— 含情感标签 + 聚类标签
- `data/cluster_top_terms.csv` —— 每个聚类的代表词
- `figures/1_comment_count.png` —— 评论数量统计图
- `figures/2_sentiment_pie.png` —— 情感比例饼图
- `figures/3_top_words.png` —— 高频词柱状图
- `figures/4_wordcloud.png` —— 词云图
- `figures/5_cluster_scatter.png` —— 主题聚类散点图
- `report/summary.txt` —— 文字版分析结论（可直接放进报告/PPT）

## 五、常见问题

**Q1：词云乱码？**
确认你的电脑里有 `C:\Windows\Fonts\simhei.ttf`，没有的话改成 `msyh.ttc` 或别的中文字体。

**Q2：matplotlib 中文显示成方块？**
`step4_visualization.py` 已配置 SimHei，如果还有问题，重启 Python 内核再试。

**Q3：SnowNLP 跑得慢？**
评论很多时（>5k）情感分析会比较慢，等 1~3 分钟即可。

**Q4：B 站接口返回 -412 / -509？**
被风控了，把 `SLEEP_RANGE` 调大一点，比如 (4, 6)，并填上 Cookie。
