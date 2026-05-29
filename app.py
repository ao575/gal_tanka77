import streamlit as st
import streamlit.components.v1 as components
import json
import random
import os
from pathlib import Path

POOL_FILE = Path(__file__).parent / "pool.json"
NGWORDS_FILE = Path(__file__).parent / "ngwords.json"
COUNTER_FILE = Path(__file__).parent / "counter.json"
REQUESTS_FILE = Path(__file__).parent / "requests.json"


def load_pool() -> list[dict]:
    if POOL_FILE.exists():
        with open(POOL_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_pool(pool: list[dict]):
    with open(POOL_FILE, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)


def load_ngwords() -> list[str]:
    if NGWORDS_FILE.exists():
        with open(NGWORDS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_ngwords(ngwords: list[str]):
    with open(NGWORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(ngwords, f, ensure_ascii=False, indent=2)


def load_requests() -> list[dict]:
    if REQUESTS_FILE.exists():
        with open(REQUESTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_requests(requests: list[dict]):
    with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)


def load_counter() -> int:
    if COUNTER_FILE.exists():
        with open(COUNTER_FILE, encoding="utf-8") as f:
            return json.load(f).get("count", 0)
    return 0


def increment_counter() -> int:
    count = load_counter() + 1
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        json.dump({"count": count}, f)
    return count


def render_tanka(selected: list[dict]) -> str:
    mora_labels = ["五", "七", "五", "七", "七"]
    cols_html = ""
    for label, entry in zip(mora_labels, selected):
        word = entry["word"]
        cols_html += f"""
<div style="display:flex;flex-direction:column;align-items:center;gap:4px;flex:1;min-width:0;">
  <span style="font-size:clamp(0.45rem,2vw,0.65rem);color:#b0a888;letter-spacing:0.05em;">{label}</span>
  <div style="
    writing-mode:vertical-rl;
    text-orientation:upright;
    font-size:clamp(1rem,5.5vw,2rem);
    font-weight:bold;
    color:#2c4a2e;
    padding:2px 4px;
    letter-spacing:0.15em;
    line-height:1.4;
  ">{word}</div>
</div>"""
    return f"""<div style="
  display:flex;
  flex-direction:row-reverse;
  justify-content:center;
  align-items:flex-start;
  gap:clamp(6px,2.5vw,24px);
  padding:clamp(14px,3vw,28px) clamp(10px,2.5vw,24px);
  background:linear-gradient(135deg,#faf7f0,#f2ede2);
  border-radius:16px;
  border:1px solid #e0d4b8;
  width:100%;
  box-sizing:border-box;
">{cols_html}</div>"""


def tanka_height(selected: list[dict]) -> int:
    max_chars = max(len(e["word"]) for e in selected)
    return max(260, 80 + max_chars * 44)


# ══════════════════════════════
# ページ設定
# ══════════════════════════════
st.set_page_config(page_title="詠み人、ギャルっす", page_icon="🎋", layout="centered")

if "counted" not in st.session_state:
    st.session_state.counted = True
    st.session_state.visitor_count = increment_counter()
else:
    st.session_state.visitor_count = load_counter()

if "pool" not in st.session_state:
    st.session_state.pool = load_pool()

if "edit_pool_idx" not in st.session_state:
    st.session_state.edit_pool_idx = None

if "edit_ng_idx" not in st.session_state:
    st.session_state.edit_ng_idx = None

pool = st.session_state.pool

# ══════════════════════════════
# サイドバー
# ══════════════════════════════
with st.sidebar:
    st.metric("訪問者数", f"{st.session_state.visitor_count:,} 回")

# ══════════════════════════════
# メインタイトル
# ══════════════════════════════
st.title("🎋 詠み人、ギャルっす")
st.caption(
    """
    「アゲな歌を詠む」を押すと、ギャル語からランダムに選ばれた単語で短歌が詠まれるよ☆\n
    みんなのリクエストで単語を増やしちゃおう！
    """)

# ══════════════════════════════
# ガチャエリア
# ══════════════════════════════
ngwords = load_ngwords()
ng_set = set(ngwords)

active_pool = [w for w in pool if w["word"] not in ng_set]
pool_5 = [w for w in active_pool if w["mora"] == 5]
pool_7 = [w for w in active_pool if w["mora"] == 7]

if st.button("アゲな歌を詠む", use_container_width=True, type="primary"):
    errors = []
    if len(pool_5) < 2:
        errors.append(f"5音の単語が足りません（必要: 2個 / 有効: {len(pool_5)}個）")
    if len(pool_7) < 3:
        errors.append(f"7音の単語が足りません（必要: 3個 / 有効: {len(pool_7)}個）")
    if errors:
        for e in errors:
            st.warning(e)
    else:
        fives = random.sample(pool_5, 2)
        sevens = random.sample(pool_7, 3)
        st.session_state.last_draw = [
            fives[0], sevens[0], fives[1], sevens[1], sevens[2]
        ]

if "last_draw" in st.session_state:
    height = tanka_height(st.session_state.last_draw)
    components.html(render_tanka(st.session_state.last_draw), height=height)

# ══════════════════════════════
# 単語リクエスト（全員）
# ══════════════════════════════
st.divider()
st.header("単語をリクエストする")
st.caption("採用されると短歌に使われるようになります。")

with st.form("request_form", clear_on_submit=True):
    rc1, rc2, rc3 = st.columns([3, 1, 1])
    req_word = rc1.text_input("単語", placeholder="例：あげポヨの")
    req_mora = rc2.selectbox("音数", [5, 7])
    req_submitted = rc3.form_submit_button("送る", use_container_width=True)

if req_submitted:
    rw = req_word.strip()
    if not rw:
        st.warning("単語を入力してください。")
    else:
        requests = load_requests()
        already_pool = any(e["word"] == rw for e in pool)
        already_req = any(e["word"] == rw for e in requests)
        if already_pool:
            st.info(f"「{rw}」はすでに採用済みです！")
        elif already_req:
            st.info(f"「{rw}」はすでにリクエスト済みです。")
        else:
            requests.append({"word": rw, "mora": req_mora})
            save_requests(requests)
            st.success(f"「{rw}」（{req_mora}音）をリクエストしました！")

# ══════════════════════════════
# 管理者ログイン（ページ末尾）
# ══════════════════════════════
st.divider()
if not st.session_state.get("is_admin"):
    with st.expander("管理者ログイン"):
        with st.form("login_form"):
            pwd = st.text_input("パスワード", type="password")
            login_btn = st.form_submit_button("ログイン", use_container_width=True)
        if login_btn:
            admin_password = os.environ.get("ADMIN_PASSWORD") or st.secrets.get("admin", {}).get("password", "")
            if pwd == admin_password:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("パスワードが違います")
else:
    if st.button("管理者ログアウト"):
        st.session_state.is_admin = False
        st.rerun()

# ══════════════════════════════
# 管理者専用エリア
# ══════════════════════════════
if st.session_state.get("is_admin"):

    # ── リクエスト審査 ──
    st.divider()
    requests = load_requests()
    pending_label = f"リクエスト審査　🔒　（{len(requests)}件）" if requests else "リクエスト審査　🔒"
    st.header(pending_label)

    if not requests:
        st.info("現在リクエストはありません。")
    else:
        for j, req in enumerate(requests):
            rc1, rc2, rc3, rc4 = st.columns([3, 1, 1, 1])
            rc1.write(req["word"])
            mora_index = 0 if req.get("mora") == 5 else 1
            approved_mora = rc2.selectbox("音数", [5, 7], index=mora_index, key=f"req_mora_{j}")
            if rc3.button("採用", key=f"approve_{j}", type="primary"):
                if not any(e["word"] == req["word"] for e in pool):
                    pool.append({"word": req["word"], "mora": approved_mora})
                    save_pool(pool)
                    st.session_state.pool = pool
                requests.pop(j)
                save_requests(requests)
                st.rerun()
            if rc4.button("却下", key=f"reject_{j}"):
                requests.pop(j)
                save_requests(requests)
                st.rerun()

    # ── 単語プール管理 ──
    st.divider()
    count_5 = len([w for w in active_pool if w["mora"] == 5])
    count_7 = len([w for w in active_pool if w["mora"] == 7])
    st.header(f"単語プール管理　🔒　（5音: {count_5}語 / 7音: {count_7}語）")

    with st.form("add_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        new_word = c1.text_input("単語", placeholder="例：あげポヨの")
        new_mora = c2.selectbox("音数", [5, 7])
        submitted = c3.form_submit_button("追加", use_container_width=True)

        if submitted:
            w = new_word.strip()
            if not w:
                st.warning("単語を入力してください。")
            elif any(e["word"] == w for e in pool):
                st.warning(f"「{w}」はすでに登録されています。")
            else:
                pool.append({"word": w, "mora": new_mora})
                save_pool(pool)
                st.success(f"「{w}」（{new_mora}音）を追加しました！")
                st.rerun()

    with st.expander("まとめて登録（改行区切り）"):
        with st.form("bulk_form", clear_on_submit=True):
            c1, c2 = st.columns([3, 1])
            bulk_text = c1.text_area("単語リスト（1行に1語）", height=120)
            bulk_mora = c2.selectbox("音数（全語に適用）", [5, 7])
            bulk_submitted = st.form_submit_button("一括追加")

            if bulk_submitted:
                new_items = [l.strip() for l in bulk_text.splitlines() if l.strip()]
                added = [w for w in new_items if not any(e["word"] == w for e in pool)]
                for w in added:
                    pool.append({"word": w, "mora": bulk_mora})
                if added:
                    save_pool(pool)
                    st.success(f"{len(added)} 語（{bulk_mora}音）を追加しました：{', '.join(added)}")
                    st.rerun()
                else:
                    st.info("追加できる新しい単語がありませんでした。")

    if pool:
        search_pool = st.text_input("🔍 絞り込み検索", key="search_pool")
        display_pool = [
            (i, w) for i, w in enumerate(pool)
            if search_pool.lower() in w["word"].lower()
        ]
        for i, w in display_pool:
            is_ng = w["word"] in ng_set
            if st.session_state.edit_pool_idx == i:
                ec1, ec2, ec3, ec4 = st.columns([3, 1, 1, 1])
                ec1.text_input("単語", value=w["word"], key=f"edit_pool_word_{i}")
                ec2.selectbox("音数", [5, 7],
                              index=0 if w.get("mora") == 5 else 1,
                              key=f"edit_pool_mora_{i}")
                if ec3.button("保存", key=f"save_pool_{i}", type="primary"):
                    new_val = st.session_state[f"edit_pool_word_{i}"].strip()
                    if new_val:
                        pool[i] = {"word": new_val, "mora": st.session_state[f"edit_pool_mora_{i}"]}
                        save_pool(pool)
                    st.session_state.edit_pool_idx = None
                    st.rerun()
                if ec4.button("取消", key=f"cancel_pool_{i}"):
                    st.session_state.edit_pool_idx = None
                    st.rerun()
            else:
                mora_label = f"{w['mora']}音" if w.get("mora") else "未設定"
                label = f"~~{w['word']}~~" if is_ng else w["word"]
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                c1.markdown(label)
                c2.caption(mora_label)
                if c3.button("編集", key=f"edit_pool_{i}"):
                    st.session_state.edit_pool_idx = i
                    st.rerun()
                if c4.button("削除", key=f"del_pool_{i}"):
                    pool.pop(i)
                    save_pool(pool)
                    st.session_state.pool = pool
                    st.rerun()

    # ── NGワード管理 ──
    st.divider()
    st.header(f"NGワード管理　🔒　（{len(ngwords)}語）")

    with st.form("add_ng_form", clear_on_submit=True):
        ng1, ng2 = st.columns([4, 1])
        new_ng = ng1.text_input("NGワード", placeholder="例：元カレ死んだ")
        ng_submitted = ng2.form_submit_button("追加", use_container_width=True)

        if ng_submitted:
            nw = new_ng.strip()
            if not nw:
                st.warning("単語を入力してください。")
            elif nw in ngwords:
                st.warning(f"「{nw}」はすでにNGワードです。")
            else:
                ngwords.append(nw)
                save_ngwords(ngwords)
                st.success(f"「{nw}」をNGワードに追加しました。")
                st.rerun()

    if ngwords:
        search_ng = st.text_input("🔍 絞り込み検索", key="search_ng")
        display_ng = [(i, w) for i, w in enumerate(ngwords) if search_ng.lower() in w.lower()]
        for i, w in display_ng:
            c1, c2 = st.columns([5, 1])
            c1.write(w)
            if c2.button("削除", key=f"del_ng_{i}"):
                ngwords.pop(i)
                save_ngwords(ngwords)
                st.rerun()
