# %% [markdown]
# # 第 1 步：爬取 B 站评论数据
#
# 本脚本完成：
# 1. 根据若干 BV 号，调用 B 站公开接口爬取视频评论
# 2. 字段包含：视频标题、BV 号、评论内容、评论时间、点赞数、回复数
# 3. 保存到 data/comments_raw.csv
#
# 备用方案：如果爬虫失败（被风控、网络问题等），可以跳过本脚本，
# 把已有的 CSV 文件放到 data/comments_raw.csv 即可，后续脚本会自动读取。
#
# Cookie 怎么填？
#   - 打开浏览器，登录 B 站（https://www.bilibili.com）
#   - 按 F12 打开开发者工具，切到「网络/Network」面板
#   - 随便刷新一下页面，点任意一个请求
#   - 在「请求标头/Request Headers」里复制整段 cookie，粘到下面 COOKIE 变量
#   - 不填也能跑，只是访问条数会受限

# %%
# ===== 单元格 1：导入依赖、基础配置 =====
import os
import time
import json
import random
import csv
import requests
import pandas as pd

# 数据保存目录
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# 把你从浏览器复制的 cookie 整段粘到这里（包括 SESSDATA 等所有字段）
# 不填也能跑，但建议填上以减少风控
# 安全提醒：Cookie 里的 SESSDATA / bili_jct 等同于账号密码，切勿提交到 GitHub 等公开仓库！
COOKIE = ""

# 请求头，模拟浏览器
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
    "Cookie": COOKIE,
}

# 每条 BV 号最多爬几页评论（每页约 20 条）
MAX_PAGES_PER_VIDEO = 8

# 每次请求间隔（秒）：B 站对高频请求会限制，建议 2~4 秒
SLEEP_RANGE = (2.0, 3.5)

# %%
# ===== 单元格 2：BV 号列表（自己从 B 站搜索关键词后挑几个视频复制 BV 号） =====
# 推荐做法（最稳定）：
#   1. 在 B 站搜索 "大学生就业"、"考研还是就业"、"考公热"、"应届生找工作"、"就业难" 等关键词
#   2. 挑几个评论比较多的视频，复制每个视频网址里的 BV 号（形如 BV1xxxxxxxxxx）
#   3. 填到下面这个列表里
#
# 搜索接口需要复杂的 wbi 签名，新手不易跑通，所以这里直接用 BV 号列表，最可靠。
BV_LIST = [
    "BV1L8Gq6hEyG",
    "BV16X3MzuEen",
    "BV1PFoiBEEZ4",
    "BV15WRjBVERR",
    "BV1Yf421Q71L",
]

print(f"待爬取视频数量：{len(BV_LIST)}")

# %%
# ===== 单元格 3：BV 号 -> avid + 视频标题 =====
def get_video_info(bvid: str):
    """
    通过 B 站视频详情接口拿到 avid 和标题。
    评论接口需要传 oid=avid。
    """
    url = "https://api.bilibili.com/x/web-interface/view"
    params = {"bvid": bvid}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = r.json()
        if data.get("code") == 0:
            d = data["data"]
            return {"bvid": bvid, "aid": d["aid"], "title": d["title"]}
        else:
            print(f"[警告] 获取视频信息失败 {bvid}: {data.get('message')}")
            return None
    except Exception as e:
        print(f"[异常] {bvid}: {e}")
        return None

# 测试一个：
sample = get_video_info(BV_LIST[0])
print(sample)

# %%
# ===== 单元格 4：爬取单个视频的评论 =====
def fetch_comments_one_video(bvid: str, title: str, aid: int, max_pages: int = 8):
    """
    使用 B 站老评论接口（最稳定）：
        https://api.bilibili.com/x/v2/reply
    参数：type=1 视频；oid=aid；pn=页码；sort=2 按热度
    返回：[{...}, {...}] 列表
    """
    api = "https://api.bilibili.com/x/v2/reply"
    rows = []
    for pn in range(1, max_pages + 1):
        params = {"type": 1, "oid": aid, "pn": pn, "sort": 2}
        try:
            r = requests.get(api, params=params, headers=HEADERS, timeout=10)
            data = r.json()
        except Exception as e:
            print(f"  第 {pn} 页请求异常：{e}")
            break

        if data.get("code") != 0:
            print(f"  第 {pn} 页接口返回失败：{data.get('message')}")
            break

        replies = (data.get("data") or {}).get("replies") or []
        if not replies:
            print(f"  第 {pn} 页无更多评论，停止")
            break

        for rep in replies:
            content = (rep.get("content") or {}).get("message", "")
            c time = rep.get("ctime", 0)  # Unix 时间戳
            like = rep.get("like", 0)
            rcount = rep.get("rcount", 0)  # 该评论下的回复数
            rows.append({
                "video_title": title,
                "bvid": bvid,
                "comment": content,
                "comment_time": time.strftime("%Y-%m-%d %H:%M:%S",
                                              time.localtime(ctime)) if ctime else "",
                "like_count": like,
                "reply_count": rcount,
            })

        # 控制请求节奏，避免被 B 站风控
        time.sleep(random.uniform(*SLEEP_RANGE))

    return rows

# %%
# ===== 单元格 5：批量爬取所有 BV，并保存 CSV =====
def crawl_all(bv_list):
    all_rows = []
    for i, bv in enumerate(bv_list, start=1):
        print(f"\n[{i}/{len(bv_list)}] 处理 {bv}")
        info = get_video_info(bv)
        if not info:
            continue
        print(f"  标题: {info['title']}")
        rows = fetch_comments_one_video(
            bvid=bv, title=info["title"], aid=info["aid"],
            max_pages=MAX_PAGES_PER_VIDEO,
        )
        print(f"  本视频抓到评论 {len(rows)} 条")
        all_rows.extend(rows)
        # 视频之间也加一点间隔
        time.sleep(random.uniform(*SLEEP_RANGE))
    return all_rows

# 真正执行爬取
results = crawl_all(BV_LIST)
print(f"\n合计评论数：{len(results)}")

# %%
# ===== 单元格 6：保存到 CSV =====
out_path = os.path.join(DATA_DIR, "comments_raw.csv")

if results:
    df = pd.DataFrame(results)
    # 去掉完全重复的评论（同一条用户复制粘贴的水军）
    df = df.drop_duplicates(subset=["bvid", "comment", "comment_time"])
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"已保存 {len(df)} 条评论到：{out_path}")
else:
    print("[备用方案] 本次没爬到数据。请把已有的评论 CSV 放到下面这个路径：")
    print(f"  {out_path}")
    print("CSV 必需字段：video_title, bvid, comment, comment_time, like_count, reply_count")
