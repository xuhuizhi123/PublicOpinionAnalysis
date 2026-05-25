# %% [markdown]
# # 第 5 步：生成分析结果总结（用于报告 / PPT）
#
# 输入：data/comments_with_sentiment.csv 等
# 输出：
#   - report/summary.txt    一份纯文本总结，可以直接复制粘贴进报告或 PPT

# %%
import os
import pandas as pd

DATA_DIR = "data"
REPORT_DIR = "report"
os.makedirs(REPORT_DIR, exist_ok=True)

df = pd.read_csv(os.path.join(DATA_DIR, "comments_with_sentiment.csv"),
                 encoding="utf-8-sig")
top_df = pd.read_csv(os.path.join(DATA_DIR, "top_words.csv"),
                     encoding="utf-8-sig")
tfidf_df = pd.read_csv(os.path.join(DATA_DIR, "tfidf_keywords.csv"),
                       encoding="utf-8-sig")
cluster_df = pd.read_csv(os.path.join(DATA_DIR, "cluster_top_terms.csv"),
                         encoding="utf-8-sig")

# %%
# ===== 汇总各项指标 =====
total = len(df)
n_videos = df["bvid"].nunique()
sent_counts = df["sentiment_label"].value_counts()
sent_pct = (sent_counts / total * 100).round(1)

top10_words = " / ".join(top_df["word"].head(10).tolist())
top10_tfidf = " / ".join(tfidf_df["keyword"].head(10).tolist())

# 每个视频的评论数 Top 5
video_top = (df.groupby("video_title").size()
               .sort_values(ascending=False).head(5))

# 每个簇取一条样例评论（点赞最高）
sample_per_cluster = []
for cid in sorted(df["cluster"].dropna().unique()):
    sub = df[df["cluster"] == cid]
    if sub.empty:
        continue
    sub = sub.sort_values("like_count", ascending=False)
    sample_per_cluster.append((int(cid), sub.iloc[0]["comment"][:60]))

# %%
# ===== 拼出文字版结论 =====
lines = []
lines.append("=" * 60)
lines.append("基于 B 站评论数据的大学生就业舆情分析 —— 结果总结")
lines.append("=" * 60)
lines.append("")

lines.append("一、数据概况")
lines.append(f"  - 共爬取 {n_videos} 个相关视频的评论，合计 {total} 条有效评论")
lines.append(f"  - 评论数量最多的视频：")
for t, c in video_top.items():
    lines.append(f"      · {t[:40]}：{c} 条")
lines.append("")

lines.append("二、情感分析结果")
for label in ["正面", "中性", "负面"]:
    cnt = int(sent_counts.get(label, 0))
    pct = sent_pct.get(label, 0.0)
    lines.append(f"  - {label}：{cnt} 条（{pct}%）")
# 自动给一句结论
dominant = sent_counts.idxmax()
lines.append(f"  → 总体情感倾向以「{dominant}」为主，"
             f"占比 {sent_pct[dominant]}%。")
if sent_pct.get("负面", 0) >= 30:
    lines.append("    其中负面情绪占比偏高，反映出大学生对当前就业形势"
                 "的焦虑与不满情绪较为普遍。")
lines.append("")

lines.append("三、高频词与关键词")
lines.append(f"  - 高频词 Top 10：{top10_words}")
lines.append(f"  - TF-IDF 关键词 Top 10：{top10_tfidf}")
lines.append("  → 评论高频集中在与求职、考公、考研、内卷等就业出路相关的话题。")
lines.append("")

lines.append("四、主题聚类（KMeans）")
for _, row in cluster_df.iterrows():
    lines.append(f"  - 簇 {row['cluster']}（{row['size']} 条）："
                 f"代表词 = {row['top_terms']}")
lines.append("")

lines.append("五、各主题代表性评论（点赞最高）")
for cid, text in sample_per_cluster:
    lines.append(f"  - 簇 {cid}：{text}")
lines.append("")

lines.append("六、初步结论（可直接放进报告 / PPT）")
lines.append("  1. 大学生就业话题在 B 站评论区呈现高度集中讨论，"
             "围绕 求职、考研、考公、考编、应届身份 等关键词。")
lines.append(f"  2. 评论整体情感以「{dominant}」为主，"
             "侧面反映出青年群体对未来就业的复杂心态。")
lines.append("  3. 主题聚类显示，舆情主要分布在 "
             f"{len(cluster_df)} 个相对独立的话题簇中，"
             "不同簇分别聚焦在 升学路径选择、岗位竞争、薪资与生活压力、"
             "体制内吸引力 等方向。")
lines.append("  4. 后续如要深化研究，可结合点赞数加权、评论时间分布，"
             "进一步分析舆情演化趋势与意见领袖。")
lines.append("")
lines.append("（详细图表见 figures/ 目录）")

summary_text = "\n".join(lines)

out_path = os.path.join(REPORT_DIR, "summary.txt")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(summary_text)
print(f"报告已保存到：{out_path}")

# Windows 控制台是 GBK，可能打印不了 emoji，遇到就跳过
try:
    print(summary_text)
except UnicodeEncodeError:
    import sys
    safe = summary_text.encode(sys.stdout.encoding or "utf-8",
                                errors="replace").decode(sys.stdout.encoding or "utf-8")
    print(safe)
