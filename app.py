import streamlit as st
import streamlit.components.v1 as components
import json
import random
from pathlib import Path

DATA_FILE = Path(__file__).parent / "words.json"
COUNTER_FILE = Path(__file__).parent / "counter.json"
REQUESTS_FILE = Path(__file__).parent / "requests.json"


def load_words() -> list[dict]:
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        result = []
        for e in data:
            if isinstance(e, str):
                result.append({"word": e, "mora": None})
            else:
                result.append({"word": e.get("word", ""), "mora": e.get("mora")})
        return result
    return []


def save_words(words: list[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)


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
<div style="display:flex;flex-direction:column;align-items:center;gap:8px;">
  <span style="font-size:0.65rem;color:#b0a888;letter-spacing:0.1em;">{label}</span>
  <div style="
    writing-mode:vertical-rl;
    text-orientation:upright;
    font-size:2rem;
    font-weight:bold;
    color:#2c4a2e;
    padding:4px 6px;
    letter-spacing:0.2em;
    line-height:1.4;
  ">{word}</div>
</div>"""
    return f"""<div style="
  display:flex;
  flex-direction:row-reverse;
  justify-content:center;
  align-items:flex-start;
  gap:24px;
  padding:28px 24px;
  background:linear-gradient(135deg,#faf7f0,#f2ede2);
  border-radius:16px;
  border:1px solid #e0d4b8;
">{cols_html}</div>"""


def tanka_height(selected: list[dict]) -> int:
    max_chars = max(len(e["word"]) for e in selected)
    return 100 + max_chars * 44


# ══════════════════════════════
# ページ設定
# ══════════════════════════════
st.set_page_config(page_title="ギャル短歌カオス", page_icon="🎋", layout="centered")

if "counted" not in st.session_state:
    st.session_state.counted = True
    st.session_state.visitor_count = increment_counter()
else:
    st.session_state.visitor_count = load_counter()

if "words" not in st.session_state:
    st.session_state.words = load_words()

if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None

words = st.session_state.words

# ══════════════════════════════
# サイドバー
# ══════════════════════════════
with st.sidebar:
    st.metric("訪問者数", f"{st.session_state.visitor_count:,} 回")

# ══════════════════════════════
# メインタイトル
# ══════════════════════════════
st.title("🎋 ギャル短歌カオス")

# ══════════════════════════════
# ガチャエリア
# ══════════════════════════════
st.header("#ギャル短歌七七")
st.caption("このウェブアプリは、愉快班様の#ギャル短歌七七のファン創作物です。")

pool_5 = [w for w in words if w["mora"] == 5]
pool_7 = [w for w in words if w["mora"] == 7]

if st.button("アゲな句を詠む", use_container_width=True, type="primary"):
    errors = []
    if len(pool_5) < 2:
        errors.append(f"5音の単語が足りません（必要: 2個 / 登録済み: {len(pool_5)}個）")
    if len(pool_7) < 3:
        errors.append(f"7音の単語が足りません（必要: 3個 / 登録済み: {len(pool_7)}個）")
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
        already_word = any(e["word"] == rw for e in words)
        already_req = any(e["word"] == rw for e in requests)
        if already_word:
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
            if pwd == st.secrets["admin"]["password"]:
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
    st.divider()

    # ── リクエスト審査 ──
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
                if not any(e["word"] == req["word"] for e in words):
                    words.append({"word": req["word"], "mora": approved_mora})
                    save_words(words)
                    st.session_state.words = words
                requests.pop(j)
                save_requests(requests)
                st.rerun()
            if rc4.button("却下", key=f"reject_{j}"):
                requests.pop(j)
                save_requests(requests)
                st.rerun()

    st.divider()
    st.header("単語を登録する　🔒")

    with st.form("add_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        new_word = c1.text_input("単語", placeholder="例：夕焼け")
        new_mora = c2.selectbox("音数", [5, 7])
        submitted = c3.form_submit_button("追加", use_container_width=True)

        if submitted:
            w = new_word.strip()
            if not w:
                st.warning("単語を入力してください。")
            elif any(e["word"] == w for e in words):
                st.warning(f"「{w}」はすでに登録されています。")
            else:
                words.append({"word": w, "mora": new_mora})
                save_words(words)
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
                added = [w for w in new_items if not any(e["word"] == w for e in words)]
                for w in added:
                    words.append({"word": w, "mora": bulk_mora})
                if added:
                    save_words(words)
                    st.success(f"{len(added)} 語（{bulk_mora}音）を追加しました：{', '.join(added)}")
                    st.rerun()
                else:
                    st.info("追加できる新しい単語がありませんでした。")

    st.divider()

    count_5 = len(pool_5)
    count_7 = len(pool_7)
    st.header(f"登録済み単語一覧（5音: {count_5}語 / 7音: {count_7}語）　🔒")

    if not words:
        st.info("まだ単語が登録されていません。")
    else:
        search = st.text_input("🔍 絞り込み検索")
        display = [
            (i, w) for i, w in enumerate(words)
            if search.lower() in w["word"].lower()
        ]

        for i, w in display:
            if st.session_state.edit_idx == i:
                ec1, ec2, ec3, ec4 = st.columns([3, 1, 1, 1])
                ec1.text_input("単語", value=w["word"], key=f"edit_word_{i}")
                ec2.selectbox("音数", [5, 7],
                              index=0 if w.get("mora") == 5 else 1,
                              key=f"edit_mora_{i}")
                if ec3.button("保存", key=f"save_{i}", type="primary"):
                    new_val = st.session_state[f"edit_word_{i}"].strip()
                    if new_val:
                        words[i] = {
                            "word": new_val,
                            "mora": st.session_state[f"edit_mora_{i}"],
                        }
                        save_words(words)
                    st.session_state.edit_idx = None
                    st.rerun()
                if ec4.button("取消", key=f"cancel_{i}"):
                    st.session_state.edit_idx = None
                    st.rerun()
            else:
                mora_label = f"{w['mora']}音" if w.get("mora") else "未設定"
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                c1.write(w["word"])
                c2.caption(mora_label)
                if c3.button("編集", key=f"edit_{i}"):
                    st.session_state.edit_idx = i
                    st.rerun()
                if c4.button("削除", key=f"del_{i}"):
                    words.pop(i)
                    save_words(words)
                    st.session_state.words = words
                    if "last_draw" in st.session_state:
                        st.session_state.last_draw = [
                            d for d in st.session_state.last_draw
                            if d["word"] != w["word"]
                        ]
                    st.rerun()
