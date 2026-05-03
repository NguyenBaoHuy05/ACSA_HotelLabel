import streamlit as st
import pandas as pd
import json
import os

# Define standard aspects for Hotel domain
ASPECTS = [
    "ROOM#CLEANLINESS", "ROOM#DESIGN", "ROOM#COMFORT", "ROOM#AMENITIES", 
    "LOCATION#ACCESS", "LOCATION#SURROUNDING", "LOCATION#VIEW", 
    "SERVICE#STAFF", "SERVICE#HOUSRKEEPING", "SERVICE#MISCELLANEOUS", 
    "FACILITIES#GENERAL","FOOD&DRINK#GENERAL", "VALUE#GENERAL", "HOTEL#GENERAL"
]
SENTIMENTS = ["None", "Positive", "Neutral", "Negative"]

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
                            for aspect, sentiment in labels.items():
                                records.append({
                                    "id": int(doc_id),
                                    "username": user,
                                    "aspect": aspect,
                                    "sentiment": sentiment
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

# Ensure index is within bounds
if total_docs > 0 and st.session_state.current_index >= total_docs:
    st.success("🎉 Bạn đã gán nhãn xong toàn bộ dữ liệu!")
    st.session_state.current_index = total_docs - 1
    
idx = st.session_state.current_index

if total_docs > 0:
    row = data_df.iloc[idx]
    doc_id = int(row['id'])
    text = row['text']
    
    st.progress((idx) / total_docs if total_docs > 0 else 0)
    st.write(f"**Câu {idx + 1} / {total_docs}**")
    
    st.info(f"{text}")
    
    # === COMPARED LABELS EXPANDER ===
    all_labels = get_all_labels()
    if not all_labels.empty:
        df_filtered = all_labels[all_labels['id'] == doc_id]
        if not df_filtered.empty:
            with st.expander("👁️ Xem nhãn của người khác cho câu này"):
                pivot_df = df_filtered.pivot(index='aspect', columns='username', values='sentiment')
                pivot_df = pivot_df.fillna("None")
                
                available_aspects = [a for a in ASPECTS if a in pivot_df.index]
                pivot_df = pivot_df.reindex(available_aspects)
                
                def highlight_conflicts(row):
                    if len(set(row)) > 1:
                        return ['background-color: rgba(255, 0, 0, 0.2)'] * len(row)
                    return [''] * len(row)
                    
                st.dataframe(pivot_df.style.apply(highlight_conflicts, axis=1), use_container_width=True)
                st.write("*(Các ô được tô màu đỏ là nơi có sự bất đồng giữa các nhãn)*")
    # =================================
    
    st.write("---")
    st.write("### Đánh giá Sentiment cho từng Aspect:")
    st.write("*(Chọn một nhãn phù hợp cho mỗi khía cạnh)*")
    
    existing_labels = get_existing_labels(username, text)
    current_labels = {}

    st.write("---")

    current_category = None
    for aspect in ASPECTS:
        category = aspect.split("#")[0]
        if current_category is not None and category != current_category:
            st.write("---")
        current_category = category
        
        col1, col2 = st.columns([1, 2])
        
        # Parsing existing labels
        existing_sentiment = existing_labels.get(aspect, "None")
        if ", " in existing_sentiment:
            existing_sentiment = existing_sentiment.split(", ")[0]
        if existing_sentiment not in ["Positive", "Neutral", "Negative", "None"]:
            existing_sentiment = "None"
        
        with col1:
            st.write(f"**{aspect}**")
        with col2:
            selected = st.radio(
                label=f"Sentiment cho {aspect}",
                options=["Positive", "Neutral", "Negative", "None"],
                index=["Positive", "Neutral", "Negative", "None"].index(existing_sentiment),
                key=f"{doc_id}_{aspect}_radio",
                horizontal=True,
                label_visibility="collapsed"
            )
            
        current_labels[aspect] = selected

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
