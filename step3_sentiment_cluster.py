# %% [markdown]
# # 第 3 步：情感分析（SnowNLP） + 主题聚类（TF-IDF + KMeans）
#
# 输入：data/comments_clean.csv
# 输出：
#   - data/comments_with_sentiment.csv   每条评论的情感标签 + 聚类标签
#   - data/cluster_top_terms.csv         每个聚类的代表性关键词

# %%
# ===== 单元格 1：导入依赖、读取清洗后的数据 =====
import os
import warnings
import numpy as np
import pandas as pd
from snownlp import SnowNLP
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD

warnings.filterwarnings("ignore")

DATA_DIR = "data"
CLEAN_PATH = os.path.join(DATA_DIR, "comments_clean.csv")
OUT_PATH = os.path.join(DATA_DIR, "comments_with_sentiment.csv")

assert os.path.exists(CLEAN_PATH), f"找不到 {CLEAN_PATH}，请先运行 step2_text_processing.py"
df = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig")
df["tokens_str"] = df["tokens_str"].fillna("")
df["comment_clean"] = df["comment_clean"].fillna("")
print(f"读取 {len(df)} 条评论")

# %%
# ===== 单元格 2：SnowNLP 情感打分 =====
# SnowNLP 返回 [0, 1] 之间的分数，越接近 1 越正面
def sentiment_score(text: str) -> float:
    text = (text or "").strip()
    if len(text) < 2:
        return 0.5  # 太短的评论看作中性
    try:
        return float(SnowNLP(text).sentiments)
    except Exception:
        return 0.5

print("正在计算情感分数（评论较多时这一步会慢一些，请稍候）...")
df["sentiment_score"] = df["comment_clean"].apply(sentiment_score)

# 三分类阈值：可以按需要调整
def label_sentiment(s: float) -> str:
    if s >= 0.6:
        return "正面"
    elif s <= 0.4:
        return "负面"
    else:
        return "中性"

df["sentiment_label"] = df["sentiment_score"].apply(label_sentiment)

print("情感分布：")
print(df["sentiment_label"].value_counts())

# %%
# ===== 单元格 3：TF-IDF 向量化（用于聚类） =====
# 用前面分好的词（空格连接）作为输入
texts_for_cluster = df[df["tokens_str"].str.len() > 0]["tokens_str"].tolist()
vectorizer = TfidfVectorizer(max_features=3000, min_df=2, max_df=0.9)
X = vectorizer.fit_transform(texts_for_cluster)
print(f"TF-IDF 矩阵尺寸：{X.shape}")

# %%
# ===== 单元格 4：KMeans 聚类 =====
# 对就业话题，4~6 个簇通常足够；这里默认 5
N_CLUSTERS = 5
km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
cluster_ids = km.fit_predict(X)

# 把 cluster 标签写回原 DataFrame：只有 tokens_str 非空的评论才参与聚类
df["cluster"] = -1
mask = df["tokens_str"].str.len() > 0
df.loc[mask, "cluster"] = cluster_ids
print("聚类分布：")
print(df["cluster"].value_counts().sort_index())

# %%
# ===== 单元格 5：每个簇的代表关键词（取簇中心权重最高的若干词） =====
terms = np.array(vectorizer.get_feature_names_out())
centers = km.cluster_centers_  # shape: (n_clusters, n_features)
TOP_N = 10

cluster_top_terms = []
for cid in range(N_CLUSTERS):
    top_idx = centers[cid].argsort()[::-1][:TOP_N]
    top_terms_for_cid = terms[top_idx].tolist()
    cluster_top_terms.append({
        "cluster": cid,
        "size": int((df["cluster"] == cid).sum()),
        "top_terms": " / ".join(top_terms_for_cid),
    })

cluster_df = pd.DataFrame(cluster_top_terms)
cluster_df.to_csv(os.path.join(DATA_DIR, "cluster_top_terms.csv"),
                  index=False, encoding="utf-8-sig")
print("每个聚类的代表关键词：")
print(cluster_df)

# %%
# ===== 单元格 6：把 TF-IDF 降到 2 维，便于后面画聚类散点图 =====
svd = TruncatedSVD(n_components=2, random_state=42)
xy = svd.fit_transform(X)

df["x_2d"] = np.nan
df["y_2d"] = np.nan
df.loc[mask, "x_2d"] = xy[:, 0]
df.loc[mask, "y_2d"] = xy[:, 1]

# %%
# ===== 单元格 7：保存最终结果 =====
df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
print(f"已保存：{OUT_PATH}")
print(df[["comment_clean", "sentiment_label", "cluster"]].head(5))
