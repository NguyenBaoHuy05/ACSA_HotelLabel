import streamlit as st
import pandas as pd
import json
import os
import requests
import re

# # Define standard aspects for Hotel domain
# ASPECTS = [
#     "ROOM#CLEANLINESS", "ROOM#DESIGN", "ROOM#COMFORT", "ROOM#AMENITIES", 
#     "LOCATION#ACCESS", "LOCATION#SURROUNDING", "LOCATION#VIEW", 
#     "SERVICE#STAFF", "SERVICE#HOUSEKEEPING", "SERVICE#MISCELLANEOUS", 
#     "FACILITIES#GENERAL","FOOD&DRINK#GENERAL", "VALUE#GENERAL", "HOTEL#GENERAL"
# ]
# SENTIMENTS = ["None", "Positive", "Neutral", "Negative"]

# # Aspect definitions (Vietnamese) for prompt context
# ASPECT_DEFINITIONS = {
#     "ROOM#CLEANLINESS":     "Độ sạch sẽ của phòng, ga giường, sàn, nhà vệ sinh.",
#     "ROOM#DESIGN":          "Phong cách, bày trí, thẩm mỹ kiến trúc bên trong phòng.",
#     "ROOM#COMFORT":         "Độ thoải mái (giường êm, cách âm, điều hòa, không gian rộng/hẹp).",
#     "ROOM#AMENITIES":       "Vật dụng trong phòng (TV, tủ lạnh, máy sấy, âm đun, khăn, bàn chải).",
#     "LOCATION#ACCESS":      "Vị trí dễ tìm, gần trung tâm, gần phương tiện công cộng.",
#     "LOCATION#SURROUNDING": "Môi trường xung quanh (ồn ào/yên tĩnh, an ninh, gần quán xá).",
#     "LOCATION#VIEW":        "Cảnh quan nhìn từ phòng hoặc khách sạn (view đẹp/xấu).",
#     "SERVICE#STAFF":        "Thái độ, kỹ năng của nhân viên (lễ tân, phục vụ, bảo vệ), các thủ tục nhận phòng, trả phòng, support, ...",
#     "SERVICE#HOUSEKEEPING": "Chất lượng và thái độ của dịch vụ dọn phòng.",
#     "SERVICE#MISCELLANEOUS":"Dịch vụ cộng thêm (giặt ủi, đặt tour, đưa đón sân bay).",
#     "FACILITIES#GENERAL":   "Tiện ích chung (thang máy, hồ bơi, gym, bãi xe, sảnh chờ, wifi khách sạn).",
#     "FOOD&DRINK#GENERAL":   "Chất lượng, hương vị bữa sáng, nhà hàng, đồ uống.",
#     "VALUE#GENERAL":        "Sự tương xứng giữa giá tiền và chất lượng nhận được.",
#     "HOTEL#GENERAL":        "Đánh giá mức độ hài lòng về khách sạn (tổng thể, ý định quay lại, giới thiệu).",
# }

ASPECTS = [
    "ROOM#CLEANLINESS",      
    "ROOM#DESIGN",
    "ROOM#COMFORT",
    "ROOM#AMENITIES",
    "LOCATION#ACCESS",
    "LOCATION#SURROUNDING",  
    "SERVICE#STAFF",
    "SERVICE#MISCELLANEOUS", 
    "FOOD&DRINK#GENERAL",
    "VALUE#GENERAL",
    "HOTEL#GENERAL"
]
SENTIMENTS = ["None", "Positive", "Neutral", "Negative"]

ASPECT_DEFINITIONS = {
    "ROOM#CLEANLINESS": (
        "Độ sạch sẽ của phòng và kết quả công việc dọn dẹp.\n"
        "Bao gồm: ga giường, sàn nhà, nhà vệ sinh, mùi phòng, vết bẩn, côn trùng.\n"
        "Cũng bao gồm: chất lượng & thái độ nhân viên housekeeping, tần suất dọn phòng, thay khăn/ga.\n"
        "Ví dụ: 'Phòng rất sạch', 'Nhà vệ sinh có mùi', 'Nhân viên dọn phòng cẩu thả', "
        "'Ga giường không được thay dù ở 3 ngày'."
    ),
    "ROOM#DESIGN": (
        "Phong cách thẩm mỹ và bài trí không gian bên trong phòng.\n"
        "Bao gồm: kiến trúc, màu sắc, nội thất, ánh sáng, cảm giác hiện đại/cũ kỹ.\n"
        "Ví dụ: 'Phòng decor rất đẹp', 'Thiết kế cũ kỹ', 'Nội thất sang trọng', 'Ánh sáng phòng tối'."
    ),
    "ROOM#COMFORT": (
        "Mức độ thoải mái khi sinh hoạt trong phòng.\n"
        "Bao gồm: chất lượng giường/gối/nệm, cách âm, nhiệt độ điều hòa, diện tích phòng, độ yên tĩnh.\n"
        "Ví dụ: 'Giường rất êm', 'Phòng cách âm kém', 'Điều hòa không mát', "
        "'Phòng rộng rãi thoải mái', 'Ngủ ngon suốt đêm'."
    ),
    "ROOM#AMENITIES": (
        "Các vật dụng và thiết bị được trang bị cố định bên trong phòng.\n"
        "Bao gồm: TV, tủ lạnh, máy sấy tóc, ấm đun nước, két sắt, đồ dùng nhà vệ sinh "
        "(dầu gội, xà phòng, bàn chải), khăn tắm, wifi trong phòng.\n"
        "Không bao gồm: tiện ích dùng chung ngoài phòng (→ SERVICE#MISCELLANEOUS).\n"
        "Ví dụ: 'Phòng có tủ lạnh mini tiện lợi', 'Không có máy sấy tóc', "
        "'Wifi phòng chập chờn', 'Đồ dùng vệ sinh đầy đủ'."
    ),
    "LOCATION#ACCESS": (
        "Vị trí và khả năng di chuyển từ khách sạn đến các điểm xung quanh.\n"
        "Bao gồm: gần trung tâm, gần phương tiện công cộng, dễ tìm đường, thuận tiện đi lại.\n"
        "Ví dụ: 'Gần chợ Bến Thành', 'Khó tìm lối vào', 'Gần bến xe buýt', "
        "'Vị trí trung tâm rất tiện'."
    ),
    "LOCATION#SURROUNDING": (
        "Môi trường và cảnh quan xung quanh khu vực khách sạn.\n"
        "Bao gồm: mức độ ồn ào/yên tĩnh, an ninh khu vực, gần quán ăn/cửa hàng, "
        "cảnh quan nhìn từ phòng hoặc ban công (view biển, view thành phố, view hồ bơi).\n"
        "Ví dụ: 'Khu vực yên tĩnh', 'Gần nhiều quán ăn ngon', 'View biển tuyệt đẹp', "
        "'Xung quanh ồn ào về đêm', 'An ninh tốt'."
    ),
    "SERVICE#STAFF": (
        "Chất lượng phục vụ của đội ngũ nhân viên khách sạn.\n"
        "Bao gồm: thái độ, sự nhiệt tình, kỹ năng giao tiếp của lễ tân, bảo vệ, phục vụ; "
        "thủ tục check-in/check-out; hỗ trợ, tư vấn, giải quyết khiếu nại.\n"
        "Không bao gồm: nhân viên dọn phòng (→ ROOM#CLEANLINESS).\n"
        "Ví dụ: 'Nhân viên lễ tân rất thân thiện', 'Check-in nhanh chóng', "
        "'Staff không biết tiếng Anh', 'Nhân viên hỗ trợ nhiệt tình'."
    ),
    "SERVICE#MISCELLANEOUS": (
        "Các dịch vụ tiện ích và cơ sở vật chất chung của khách sạn (ngoài phòng).\n"
        "Bao gồm tiện ích cố định: thang máy, hồ bơi, gym, bãi xe, sảnh chờ, wifi khu vực chung.\n"
        "Bao gồm dịch vụ theo yêu cầu: giặt ủi, đặt tour, đưa đón sân bay, thuê xe.\n"
        "Ví dụ: 'Hồ bơi sạch và rộng', 'Bãi xe miễn phí', 'Dịch vụ đưa đón sân bay tiện lợi', "
        "'Wifi sảnh yếu', 'Gym có đầy đủ thiết bị'."
    ),
    "FOOD&DRINK#GENERAL": (
        "Chất lượng đồ ăn và thức uống tại khách sạn.\n"
        "Bao gồm: bữa sáng buffet, nhà hàng trong khách sạn, bar, đồ ăn nhẹ, "
        "hương vị, sự đa dạng món ăn, chất lượng nguyên liệu.\n"
        "Ví dụ: 'Buffet sáng phong phú', 'Đồ ăn nhạt nhẽo', "
        "'Nhà hàng view đẹp', 'Cà phê buổi sáng rất ngon'."
    ),
    "VALUE#GENERAL": (
        "Sự tương xứng giữa mức giá và chất lượng thực tế nhận được.\n"
        "Bao gồm: đánh giá về giá phòng, khuyến mãi, so sánh giá với chất lượng.\n"
        "Lưu ý: aspect này có thể trái chiều với HOTEL#GENERAL "
        "(hài lòng về trải nghiệm nhưng thấy đắt, hoặc ngược lại).\n"
        "Ví dụ: 'Giá hơi cao so với chất lượng', 'Rất đáng tiền', "
        "'Tìm được deal tốt', 'Không xứng với mức giá bỏ ra'."
    ),
    "HOTEL#GENERAL": (
        "Đánh giá tổng thể về trải nghiệm lưu trú tại khách sạn.\n"
        "Bao gồm: mức độ hài lòng chung, ý định quay lại, sẵn sàng giới thiệu cho người khác, "
        "cảm nhận tổng quát không thuộc aspect cụ thể nào.\n"
        "Chỉ dùng khi câu đánh giá mang tính tổng kết, không thể gán vào aspect cụ thể.\n"
        "Ví dụ: 'Sẽ quay lại lần sau', 'Rất hài lòng với chuyến nghỉ', "
        "'Khách sạn tuyệt vời, recommend cho mọi người', 'Trải nghiệm tệ, không quay lại'."
    ),
}
    
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma4"


def get_gemma_suggestions(text: str) -> dict:
    """Call local Ollama Gemma model and parse sentiment suggestions for all aspects."""
    aspect_list = "\n".join(
        [f"- {asp}: {ASPECT_DEFINITIONS[asp]}" for asp in ASPECTS]
    )
    prompt = f"""Bạn là chuyên gia phân tích cảm xúc (Aspect-Category Sentiment Analysis - ACSA) cho lĩnh vực khách sạn.

Nhiệm vụ: Phân tích đánh giá dưới đây theo các bước sau:
1. Suy nghĩ (Reasoning): Đọc hiểu đánh giá, trích xuất các ý chính liên quan đến từng khía cạnh khách sạn.
2. Gán nhãn (Labeling): Xác định cảm xúc (Positive, Neutral, Negative, None) cho từng khía cạnh dựa trên suy nghĩ vừa thực hiện.

=== CÁC KHÍA CẠNH CẦN ĐÁNH GIÁ ===
{aspect_list}

=== ĐÁNH GIÁ CỦA KHÁCH ===
\"{text}\"

=== YÊU CẦU ĐẦU RA ===
Trả về JSON với đúng cấu trúc sau (chỉ JSON, không text thêm):
{{
  "reasoning": "Phân tích chi tiết các ý chính từ đánh giá và liên kết chúng với các khía cạnh (ví dụ: 'Khách khen giường êm -> ROOM#COMFORT=Positive; Khách chê nhân viên chậm -> SERVICE#STAFF=Negative').",
  "ROOM#CLEANLINESS": "Positive" | "Neutral" | "Negative" | "None",
  "ROOM#DESIGN": "Positive" | "Neutral" | "Negative" | "None",
  "ROOM#COMFORT": "Positive" | "Neutral" | "Negative" | "None",
  "ROOM#AMENITIES": "Positive" | "Neutral" | "Negative" | "None",
  "LOCATION#ACCESS": "Positive" | "Neutral" | "Negative" | "None",
  "LOCATION#SURROUNDING": "Positive" | "Neutral" | "Negative" | "None",
  "LOCATION#VIEW": "Positive" | "Neutral" | "Negative" | "None",
  "SERVICE#STAFF": "Positive" | "Neutral" | "Negative" | "None",
  "SERVICE#HOUSEKEEPING": "Positive" | "Neutral" | "Negative" | "None",
  "SERVICE#MISCELLANEOUS": "Positive" | "Neutral" | "Negative" | "None",
  "FACILITIES#GENERAL": "Positive" | "Neutral" | "Negative" | "None",
  "FOOD&DRINK#GENERAL": "Positive" | "Neutral" | "Negative" | "None",
  "VALUE#GENERAL": "Positive" | "Neutral" | "Negative" | "None",
  "HOTEL#GENERAL": "Positive" | "Neutral" | "Negative" | "None"
}}

Quy tắc:
- Điền trường "reasoning" TRƯỚC (suy nghĩ, phân tích câu), sau đó mới điền các nhãn aspect dựa trên reasoning đó
- Chỉ dùng 4 giá trị cho các aspect: "Positive", "Neutral", "Negative", "None"
- "None" = không đề cập hoặc không thể xác định
- Trường "reasoning" chỉ đề cập các aspect có nhãn khác None, theo dạng: "aspect=Nhãn vì [lý do]"
- Lưu ý không dùng nhãn "Neutral" tùy tiện khi trong câu không có đề cập
- Chỉ xuất ra JSON, không thêm gì khác"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
        response.raise_for_status()
        raw = response.json().get("response", "")
        # Extract JSON block robustly (allow nested strings in reasoning field)
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            suggestions = json.loads(json_match.group())
            # Extract and preserve reasoning separately
            reasoning = suggestions.pop("reasoning", "")
            # Validate sentiment values
            validated = {}
            for asp in ASPECTS:
                val = suggestions.get(asp, "None")
                if val not in ["Positive", "Neutral", "Negative", "None"]:
                    val = "None"
                validated[asp] = val
            if reasoning:
                validated["__reasoning__"] = reasoning
            return validated
        else:
            return {}
    except requests.exceptions.ConnectionError:
        return {"__error__": "connection"}
    except requests.exceptions.Timeout:
        return {"__error__": "timeout"}
    except Exception as e:
        return {"__error__": str(e)}

def get_user_file(username):
    safe_username = "".join([c for c in username if c.isalnum() or c == '_']).strip()
    if not safe_username:
        safe_username = "default_user"
    return f"{safe_username}.json"

def load_json(username):
    file_path = get_user_file(username)
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(username, data):
    with open(get_user_file(username), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    st.sidebar.markdown("---")
    uploaded_file = st.sidebar.file_uploader("📂 Tải dữ liệu lên (CSV/XLSX)", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            else:
                df = pd.read_excel(uploaded_file)
            
            # Require 'text' column
            if 'text' not in df.columns:
                st.sidebar.error("❌ File tải lên bắt buộc phải có cột tên là 'text' chứa câu review!")
                return pd.DataFrame()
                
            # Auto-generate 'id' if not exists
            if 'id' not in df.columns:
                df['id'] = range(1, len(df) + 1)
                
            df.to_csv("current_data.csv", index=False, encoding='utf-8-sig')
            st.sidebar.success("✅ Đã tải và lưu dữ liệu mới thành công!")
            return df
        except Exception as e:
            st.sidebar.error(f"Lỗi đọc file: {e}")
            return pd.DataFrame()
            
    if os.path.exists("current_data.csv"):
        return pd.read_csv("current_data.csv", encoding='utf-8-sig')
    else:
        return pd.DataFrame()

def get_progress(username):
    if not os.path.exists('progress.json'):
        return 0
    with open('progress.json', 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            return data.get(username, 0)
        except:
            return 0

def save_progress(username, index):
    data = {}
    if os.path.exists('progress.json'):
        with open('progress.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                pass
    data[username] = index
    with open('progress.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_labels(username, doc_id, text, labels_dict):
    data = load_json(username)
    filtered_labels = {k: v for k, v in labels_dict.items() if v != "None"}
    
    found = False
    for item in data:
        if item.get("comment") == text:
            item["label"] = filtered_labels
            found = True
            break
            
    if not found:
        data.append({
            "comment": text,
            "label": filtered_labels
        })
        
    save_json(username, data)

def get_existing_labels(username, text):
    data = load_json(username)
    for item in data:
        if item.get("comment") == text:
            return item.get("label", {})
    return {}
    
def get_all_labels():
    records = []
    text_to_id = {}
    if os.path.exists("current_data.csv"):
        try:
            df = pd.read_csv("current_data.csv", encoding='utf-8-sig')
            text_to_id = dict(zip(df['text'], df['id']))
        except:
            pass
            
    for f in os.listdir('.'):
        if f.endswith('.json') and f not in ['progress.json', 'labeling_data.json']:
            user = f.replace('.json', '')
            with open(f, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    if isinstance(data, list):
                        for item in data:
                            text = item.get("comment", "")
                            labels = item.get("label", {})
                            doc_id = text_to_id.get(text, -1)
                            if labels:
                                for aspect, sentiment in labels.items():
                                    records.append({
                                        "id": int(doc_id),
                                        "username": user,
                                        "aspect": aspect,
                                        "sentiment": sentiment
                                    })
                            else:
                                # User đã gán nhãn câu này nhưng tất cả đều None
                                # Vẫn thêm để hiện trong bảng so sánh
                                for aspect in ASPECTS:
                                    records.append({
                                        "id": int(doc_id),
                                        "username": user,
                                        "aspect": aspect,
                                        "sentiment": "None"
                                    })
                except:
                    pass
    if records:
        return pd.DataFrame(records)
    else:
        # Return empty dataframe with correct columns
        return pd.DataFrame(columns=["id", "username", "aspect", "sentiment"])

st.set_page_config(page_title="ACSA Labeling Tool", layout="wide")

st.title("🏷️ Hotel ACSA Data Labeling Tool")

# Sidebar for login and navigation
st.sidebar.header("User Settings")
username = st.sidebar.text_input("Nhập tên của bạn (Username):")

# File upload is managed here
data_df = load_data()
total_docs = len(data_df)

if not username:
    st.warning("Vui lòng nhập tên của bạn ở thanh bên trái (Sidebar) để bắt đầu gán nhãn!")
    st.stop()

if "current_index" not in st.session_state:
    st.session_state.current_index = get_progress(username)

if "auto_label_running" not in st.session_state:
    st.session_state.auto_label_running = False

if "auto_label_done" not in st.session_state:
    # Set of doc_ids already labeled in this auto session (prevents double-call on re-render)
    st.session_state.auto_label_done = set()

# Ensure index is within bounds
if total_docs > 0 and st.session_state.current_index >= total_docs:
    st.success("🎉 Bạn đã gán nhãn xong toàn bộ dữ liệu!")
    st.session_state.auto_label_running = False
    st.session_state.current_index = total_docs - 1
    
idx = st.session_state.current_index

if total_docs > 0:
    row = data_df.iloc[idx]
    doc_id = int(row['id'])
    text = row['text']
    
    st.progress((idx) / total_docs if total_docs > 0 else 0)

    col_prog, col_jump = st.columns([3, 1])
    with col_prog:
        st.write(f"**Câu {idx + 1} / {total_docs}**")
    with col_jump:
        jump_to = st.number_input(
            "Nhảy đến câu:",
            min_value=1, max_value=total_docs,
            value=idx + 1,
            step=1,
            label_visibility="collapsed",
            help="Nhập số câu muốn chuyển đến rồi nhấn Enter"
        )
        if jump_to - 1 != idx:
            st.session_state.current_index = int(jump_to) - 1
            save_progress(username, st.session_state.current_index)
            st.rerun()

    st.info(f"{text}")

    # === GEMMA AI SUGGESTION BUTTON + CONTINUOUS AUTO-LABEL ===
    suggest_key = f"gemma_suggest_{doc_id}"
    if suggest_key not in st.session_state:
        st.session_state[suggest_key] = None

    col_btn1, col_btn2, col_status = st.columns([1.2, 1.5, 3.5])

    # --- Single suggestion button ---
    with col_btn1:
        if st.button("🤖 Gợi ý Gemma", key=f"btn_gemma_{doc_id}", use_container_width=True,
                     disabled=st.session_state.auto_label_running):
            with st.spinner("Đang phân tích với Gemma... ⏳"):
                suggestions = get_gemma_suggestions(text)
                if "__error__" in suggestions:
                    err = suggestions["__error__"]
                    if err == "connection":
                        st.session_state[suggest_key] = {"__error__": "❌ Không kết nối được Ollama. Hãy chắc chắn Ollama đang chạy (`ollama serve`) và model đã tải (`ollama pull gemma3:4b`)."}
                    else:
                        st.session_state[suggest_key] = {"__error__": f"❌ Lỗi: {err}"}
                else:
                    st.session_state[suggest_key] = suggestions
                    for asp, sentiment in suggestions.items():
                        radio_key = f"{doc_id}_{asp}_radio"
                        st.session_state[radio_key] = sentiment

    # --- Continuous auto-label / Stop button ---
    with col_btn2:
        if not st.session_state.auto_label_running:
            if st.button("⚡ Gán nhãn liên tục", key="btn_auto_label_start", use_container_width=True):
                st.session_state.auto_label_running = True
                st.session_state.auto_label_done = set()  # reset done-set on new session
                st.rerun()
        else:
            if st.button("⏹️ Dừng", key="btn_auto_label_stop", use_container_width=True, type="primary"):
                st.session_state.auto_label_running = False
                st.session_state.auto_label_done = set()
                st.rerun()

    # --- Status column ---
    with col_status:
        if st.session_state.auto_label_running:
            st.info(f"⚡ Đang gán nhãn liên tục... Câu {idx + 1}/{total_docs}. Bấm **Dừng** để dừng lại.")
        elif st.session_state[suggest_key] is not None:
            if "__error__" in st.session_state[suggest_key]:
                st.error(st.session_state[suggest_key]["__error__"])
            else:
                non_none = {k: v for k, v in st.session_state[suggest_key].items()
                            if v != "None" and not k.startswith("__")}
                if non_none:
                    tags = " ".join([f"`{k}:{v}`" for k, v in non_none.items()])
                    st.success(f"✅ Gemma đã gợi ý! Các aspect được phát hiện: {tags}")
                else:
                    st.info("ℹ️ Gemma không phát hiện aspect nào rõ ràng trong câu này.")

    # --- Continuous auto-label loop logic ---
    # Guard: skip if this doc_id was already processed in this auto session
    if st.session_state.auto_label_running and doc_id not in st.session_state.auto_label_done:
        # Mark as in-progress immediately (persists across any unexpected re-renders)
        st.session_state.auto_label_done.add(doc_id)

        with st.spinner(f"⚡ Gemma đang tự động gán nhãn câu {idx + 1}/{total_docs}... (tối đa 3 phút/câu)"):
            auto_suggestions = get_gemma_suggestions(text)

        if "__error__" in auto_suggestions:
            err = auto_suggestions["__error__"]
            if err == "connection":
                st.error("❌ Không kết nối được Ollama. Đã dừng gán nhãn liên tục.")
                st.session_state.auto_label_running = False
                st.session_state.auto_label_done = set()
                st.rerun()
            elif err == "timeout":
                st.warning(f"⚠️ Câu {idx + 1} bị timeout (>3 phút), bỏ qua và tiếp tục...")
                if idx < total_docs - 1:
                    st.session_state.current_index += 1
                    save_progress(username, st.session_state.current_index)
                    st.rerun()
                else:
                    st.session_state.auto_label_running = False
                    st.session_state.auto_label_done = set()
                    st.success("🎉 Gán nhãn liên tục hoàn tất toàn bộ dữ liệu!")
                    st.rerun()
            else:
                st.error(f"❌ Lỗi khi gán nhãn liên tục: {err}. Đã dừng.")
                st.session_state.auto_label_running = False
                st.session_state.auto_label_done = set()
                st.rerun()
        else:
            # Apply labels to radio widget states
            auto_labels = {}
            for asp in ASPECTS:
                sentiment = auto_suggestions.get(asp, "None")
                st.session_state[f"{doc_id}_{asp}_radio"] = sentiment
                auto_labels[asp] = sentiment
            # Save this sentence
            save_labels(username, doc_id, text, auto_labels)
            # Advance to next sentence or finish
            if idx < total_docs - 1:
                st.session_state.current_index += 1
                save_progress(username, st.session_state.current_index)
                st.rerun()  # st.rerun() raises exception → code below does NOT run
            else:
                st.session_state.auto_label_running = False
                st.session_state.auto_label_done = set()
                st.success("🎉 Gán nhãn liên tục hoàn tất toàn bộ dữ liệu!")
                st.rerun()

    # Display reasoning if available (only when not in auto mode)
    reasoning_text = (
        st.session_state[suggest_key].get("__reasoning__", "")
        if st.session_state[suggest_key] and "__error__" not in st.session_state[suggest_key]
           and not st.session_state.auto_label_running
        else ""
    )
    if reasoning_text:
        with st.expander("💡 Giải thích lựa chọn của Gemma", expanded=True):
            st.markdown(reasoning_text)
    # ===================================

    # === COMPARED LABELS EXPANDER ===
    all_labels = get_all_labels()
    if not all_labels.empty:
        df_filtered = all_labels[all_labels['id'] == doc_id]
        if not df_filtered.empty:
            pivot_df = df_filtered.pivot(index='aspect', columns='username', values='sentiment')
            pivot_df = pivot_df.fillna("None")

            available_aspects = [a for a in ASPECTS if a in pivot_df.index]
            pivot_df = pivot_df.reindex(available_aspects)

            # Ẩn các hàng mà tất cả người dùng đều nhãn "None"
            pivot_df = pivot_df[~(pivot_df == "None").all(axis=1)]

            if not pivot_df.empty:
                with st.expander("👁️ Xem & chỉnh nhãn của người khác cho câu này"):
                    # Highlight conflicts (read-only view)
                    def highlight_conflicts(row):
                        if len(set(row.dropna())) > 1:
                            return ['background-color: rgba(255, 0, 0, 0.2)'] * len(row)
                        return [''] * len(row)

                    st.dataframe(pivot_df.style.apply(highlight_conflicts, axis=1), use_container_width=True)
                    st.caption("*(Các ô được tô màu đỏ là nơi có sự bất đồng giữa các nhãn)*")

                    st.write("**✏️ Chỉnh sửa nhãn:**")

                    # Build column_config: each user column gets a SelectboxColumn
                    sentiment_options = ["None", "Positive", "Neutral", "Negative"]
                    col_config = {}
                    for col_name in pivot_df.columns:
                        col_config[col_name] = st.column_config.SelectboxColumn(
                            label=col_name,
                            options=sentiment_options,
                            required=True,
                        )

                    edited_df = st.data_editor(
                        pivot_df,
                        column_config=col_config,
                        use_container_width=True,
                        key=f"compare_editor_{doc_id}",
                    )

                    # Detect changes and persist them back to the relevant user JSON
                    if not edited_df.equals(pivot_df):
                        for col_user in edited_df.columns:
                            for asp in edited_df.index:
                                old_val = pivot_df.at[asp, col_user] if asp in pivot_df.index else "None"
                                new_val = edited_df.at[asp, col_user]
                                if old_val != new_val:
                                    # Load that user's data and update
                                    user_data = load_json(col_user)
                                    found = False
                                    for item in user_data:
                                        if item.get("comment") == text:
                                            if new_val == "None":
                                                item["label"].pop(asp, None)
                                            else:
                                                item["label"][asp] = new_val
                                            found = True
                                            break
                                    if not found and new_val != "None":
                                        user_data.append({"comment": text, "label": {asp: new_val}})
                                    save_json(col_user, user_data)
                        st.toast("✅ Đã lưu thay đổi nhãn!", icon="💾")
                        st.rerun()

                    st.caption("💡 Click vào ô bất kỳ để chọn lại sentiment. Thay đổi được lưu tự động.")
    # =================================
    
    st.write("---")
    st.write("### Đánh giá Sentiment cho từng Aspect:")
    st.write("*(Chọn một nhãn phù hợp cho mỗi khía cạnh)*")
    
    existing_labels = get_existing_labels(username, text)
    current_labels = {}

    # Pre-initialize session state for each radio key to avoid
    # Streamlit conflict between `index=` default and Session State API.
    # Only set if NOT already present (preserves Gemma suggestions).
    for _asp in ASPECTS:
        _radio_key = f"{doc_id}_{_asp}_radio"
        if _radio_key not in st.session_state:
            _existing = existing_labels.get(_asp, "None")
            if ", " in _existing:
                _existing = _existing.split(", ")[0]
            if _existing not in ["Positive", "Neutral", "Negative", "None"]:
                _existing = "None"
            st.session_state[_radio_key] = _existing

    st.write("---")

    current_category = None
    for aspect in ASPECTS:
        category = aspect.split("#")[0]
        if current_category is not None and category != current_category:
            st.write("---")
        current_category = category

        col1, col2 = st.columns([1, 2])

        with col1:
            st.write("")
            st.write(f"**{aspect}**")
        with col2:
            # No `index=` — value comes entirely from session state (pre-initialized above)
            selected = st.radio(
                label=f"Sentiment cho {aspect}",
                options=["Positive", "Neutral", "Negative", "None"],
                key=f"{doc_id}_{aspect}_radio",
                horizontal=True,
                label_visibility="collapsed"
            )

        current_labels[aspect] = selected
        st.write("")  # spacing between rows

    st.write("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("⬅️ Quay lại (Prev)", disabled=(idx == 0), use_container_width=True):
            save_labels(username, doc_id, text, current_labels)
            st.session_state.current_index -= 1
            save_progress(username, st.session_state.current_index)
            st.rerun()
            
    with col2:
        if st.button("Lưu & Tiếp theo ➡️", type="primary", use_container_width=True):
            save_labels(username, doc_id, text, current_labels)
            if idx < total_docs - 1:
                st.session_state.current_index += 1
                save_progress(username, st.session_state.current_index)
            st.rerun()
else:
    st.warning("Không có dữ liệu để gán nhãn. Vui lòng tải dữ liệu của bạn lên ở cột bên trái.")
