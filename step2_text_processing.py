# %% [markdown]
# # 第 2 步：文本清洗 + 中文分词 + 高频词 + TF-IDF
#
# 输入：data/comments_raw.csv
# 输出：
#   - data/comments_clean.csv     清洗后的评论（含分词列）
#   - data/top_words.csv          高频词 Top 50
#   - data/tfidf_keywords.csv     TF-IDF 关键词 Top 50

# %%
# ===== 单元格 1：导入依赖、读取数据 =====
import os
import re
import pandas as pd
import jieba
import jieba.analyse
from collections import Counter

DATA_DIR = "data"
RAW_PATH = os.path.join(DATA_DIR, "comments_raw.csv")
CLEAN_PATH = os.path.join(DATA_DIR, "comments_clean.csv")

assert os.path.exists(RAW_PATH), f"找不到 {RAW_PATH}，请先运行 step1_crawler.py 或放入备用 CSV"

df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
print(f"读取评论 {len(df)} 条")
print(df.head(3))

# %%
# ===== 单元格 2：文本清洗 =====
def clean_text(text: str) -> str:
    """
    简单清洗：去掉 URL、@用户、表情符 [xxx]、特殊符号、纯数字串。
    保留中文、英文、数字、常见标点。
    """
    if not isinstance(text, str):
        return ""
    text = re.sub(r"https?://\S+", "", text)            # URL
    text = re.sub(r"@[\w\-·]+", "", text)               # @用户名
    text = re.sub(r"\[[^\[\]]{1,15}\]", "", text)       # B 站表情 [doge]
    text = re.sub(r"[^一-龥A-Za-z0-9，。！？、；：""''（）《》 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df["comment_clean"] = df["comment"].astype(str).apply(clean_text)

# 过滤掉过短或空的评论（少于 4 个字基本是"哈哈"这种噪声）
df = df[df["comment_clean"].str.len() >= 4].reset_index(drop=True)
print(f"清洗后剩余 {len(df)} 条")

# %%
# ===== 单元格 3：加载停用词 =====
STOPWORDS_PATH = "stopwords.txt"

def load_stopwords(path):
    if not os.path.exists(path):
        # 找不到文件时，给一个最小内置词表保底
        return set(list("的了是我也就都还很在和也对又啊吗呢吧把就这那有没要会能去做"))
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

stopwords = load_stopwords(STOPWORDS_PATH)
print(f"停用词数量：{len(stopwords)}")

# %%
# ===== 单元格 4：分词 + 去停用词 =====
# 给 jieba 加几个领域词，避免被切开
for w in ["大学生", "应届生", "考公", "考研", "就业难", "内卷", "上岸",
          "应届", "国考", "省考", "考编", "三支一扶", "选调生",
          "大厂", "外包", "实习", "秋招", "春招"]:
    jieba.add_word(w)

def tokenize(text: str):
    words = jieba.lcut(text)
    return [w for w in words
            if len(w) >= 2 and w not in stopwords and not w.isspace()]

df["tokens"] = df["comment_clean"].apply(tokenize)
df["tokens_str"] = df["tokens"].apply(lambda xs: " ".join(xs))

# 保存清洗 + 分词结果
df.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig")
print(f"已保存清洗结果：{CLEAN_PATH}")
print(df[["comment_clean", "tokens_str"]].head(3))

# %%
# ===== 单元格 5：高频词 Top 50 =====
all_words = []
for toks in df["tokens"]:
    all_words.extend(toks)

counter = Counter(all_words)
top_words = counter.most_common(50)

top_df = pd.DataFrame(top_words, columns=["word", "count"])
top_df.to_csv(os.path.join(DATA_DIR, "top_words.csv"),
              index=False, encoding="utf-8-sig")
print("Top 20 高频词：")
print(top_df.head(20))

# %%
# ===== 单元格 6：TF-IDF 关键词 Top 50 =====
# jieba.analyse 自带 TF-IDF，传入整段语料即可
corpus = " ".join(df["comment_clean"].tolist())
keywords = jieba.analyse.extract_tags(
    corpus,
    topK=50,
    withWeight=True,
    allowPOS=("n", "nr", "ns", "nt", "nz", "v", "vn", "a", "an", "i"),  # 词性过滤
)
tfidf_df = pd.DataFrame(keywords, columns=["keyword", "weight"])
tfidf_df.to_csv(os.path.join(DATA_DIR, "tfidf_keywords.csv"),
                index=False, encoding="utf-8-sig")
print("TF-IDF Top 20 关键词：")
print(tfidf_df.head(20))
