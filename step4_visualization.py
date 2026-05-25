# %% [markdown]
# # 第 4 步：可视化图表
#
# 输入：
#   - data/comments_with_sentiment.csv
#   - data/top_words.csv
# 输出（保存在 figures/）：
#   1. 评论数量统计图（按视频）
#   2. 情感比例饼图
#   3. 高频词柱状图
#   4. 词云图
#   5. 主题聚类结果散点图

# %%
# ===== 单元格 1：导入依赖、配置中文字体 =====
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # 非交互后端：不弹窗，只保存图片，命令行运行更友好
import matplotlib.pyplot as plt
from matplotlib import rcParams
from wordcloud import WordCloud

DATA_DIR = "data"
FIG_DIR = "figures"
os.makedirs(FIG_DIR, exist_ok=True)

# 中文字体配置：Windows 自带 SimHei (黑体)
rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
rcParams["axes.unicode_minus"] = False

# 词云需要一个中文字体文件路径，Windows 下常见路径
FONT_PATH_CANDIDATES = [
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simsun.ttc",
]
FONT_PATH = next((p for p in FONT_PATH_CANDIDATES if os.path.exists(p)), None)

df = pd.read_csv(os.path.join(DATA_DIR, "comments_with_sentiment.csv"),
                 encoding="utf-8-sig")
top_df = pd.read_csv(os.path.join(DATA_DIR, "top_words.csv"),
                     encoding="utf-8-sig")
cluster_df = pd.read_csv(os.path.join(DATA_DIR, "cluster_top_terms.csv"),
                         encoding="utf-8-sig")
print(f"读入 {len(df)} 条评论")

# %%
# ===== 单元格 2：图1 - 评论数量统计图（按视频） =====
counts = df.groupby("video_title").size().sort_values(ascending=True)

# 标题太长就截断一点，避免 y 轴溢出
labels = [t[:18] + ("…" if len(t) > 18 else "") for t in counts.index]

fig, ax = plt.subplots(figsize=(9, max(3, 0.5 * len(counts))))
ax.barh(labels, counts.values, color="#4C9EE5")
ax.set_xlabel("评论条数")
ax.set_title("各视频评论数量统计", fontsize=13)
for i, v in enumerate(counts.values):
    ax.text(v, i, f" {v}", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "1_comment_count.png"), dpi=150)
plt.show()

# %%
# ===== 单元格 3：图2 - 情感比例饼图 =====
sent_counts = df["sentiment_label"].value_counts()
colors = {"正面": "#5BC85B", "中性": "#A0A0A0", "负面": "#E36363"}
pie_colors = [colors.get(k, "#8888CC") for k in sent_counts.index]

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(
    sent_counts.values,
    labels=sent_counts.index,
    colors=pie_colors,
    autopct="%1.1f%%",
    startangle=90,
    textprops={"fontsize": 12},
)
ax.set_title("评论情感比例", fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "2_sentiment_pie.png"), dpi=150)
plt.show()

# %%
# ===== 单元格 4：图3 - 高频词柱状图（Top 20） =====
top20 = top_df.head(20).iloc[::-1]  # 反转一下，最高的在最上面

fig, ax = plt.subplots(figsize=(8, 7))
ax.barh(top20["word"], top20["count"], color="#F0A04B")
ax.set_xlabel("出现次数")
ax.set_title("评论高频词 Top 20", fontsize=13)
for i, (w, c) in enumerate(zip(top20["word"], top20["count"])):
    ax.text(c, i, f" {c}", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "3_top_words.png"), dpi=150)
plt.show()

# %%
# ===== 单元格 5：图4 - 词云图 =====
freq = dict(zip(top_df["word"], top_df["count"]))

wc = WordCloud(
    font_path=FONT_PATH,           # 中文字体，必须设置否则会乱码
    width=1200, height=700,
    background_color="white",
    max_words=200,
    colormap="viridis",
)
wc.generate_from_frequencies(freq)

fig, ax = plt.subplots(figsize=(12, 7))
ax.imshow(wc, interpolation="bilinear")
ax.axis("off")
ax.set_title("评论词云", fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "4_wordcloud.png"), dpi=150)
plt.show()

# %%
# ===== 单元格 6：图5 - 主题聚类散点图 =====
sub = df.dropna(subset=["x_2d", "y_2d"])
fig, ax = plt.subplots(figsize=(9, 7))

# 给每个簇一个颜色
clusters = sorted(sub["cluster"].unique())
cmap = plt.get_cmap("tab10")

for i, cid in enumerate(clusters):
    seg = sub[sub["cluster"] == cid]
    # 从 cluster_top_terms 里取这个簇的 top 词，作为 legend
    row = cluster_df[cluster_df["cluster"] == cid]
    label_text = f"簇 {cid}"
    if not row.empty:
        terms_short = " / ".join(row.iloc[0]["top_terms"].split(" / ")[:4])
        label_text += f"：{terms_short}"
    ax.scatter(seg["x_2d"], seg["y_2d"],
               s=12, alpha=0.6, color=cmap(i % 10),
               label=label_text)

ax.set_title("评论主题聚类（TF-IDF + KMeans，2D 投影）", fontsize=13)
ax.set_xlabel("Component 1")
ax.set_ylabel("Component 2")
ax.legend(loc="best", fontsize=9, framealpha=0.85)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "5_cluster_scatter.png"), dpi=150)
plt.show()

print(f"\n所有图表已保存到 {FIG_DIR}/ 目录")
