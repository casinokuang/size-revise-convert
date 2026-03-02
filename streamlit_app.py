import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="自定義轉置工具", layout="wide")

st.title("🔄 彈性二維轉一維工具")
st.markdown("上傳檔案後，你可以**手動挑選**哪些是固定欄位（如款號、客戶、顏色）。")

# --- 1. 檔案上傳 ---
uploaded_file = st.file_uploader("選擇要上傳的檔案", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df.columns = df.columns.astype(str)
        st.subheader("1. 原始資料預覽")
        st.dataframe(df.head(5))

        # --- 2. 設定固定欄位 ---
        all_columns = df.columns.tolist()
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            id_vars = st.multiselect(
                "請勾選【固定不動】的資訊欄位：", 
                options=all_columns,
                default=all_columns[:3] if len(all_columns) >= 3 else [all_columns[0]]
            )

        # --- 3. 執行轉換 ---
        if id_vars:
            if st.button("🚀 執行轉換並格式化日期", type="primary"):
                # 自動判斷被選取的欄位中是否有「日期」相關字眼
                date_cols = [c for c in id_vars if "日期" in c or "Date" in id_vars or "date" in id_vars]

                # 轉換邏輯
                value_vars = [col for col in all_columns if col not in id_vars]
                df_melted = df.melt(id_vars=id_vars, value_vars=value_vars, var_name="屬性/尺碼", value_name="數量/值")
                
                # 清洗空值
                df_melted = df_melted.dropna(subset=["數量/值"])
                df_melted = df_melted[df_melted["數量/值"] != 0]

                # 【核心改動：格式化日期】
                for col in date_cols:
                    try:
                        # 先轉成 datetime 物件
                        df_melted[col] = pd.to_datetime(df_melted[col])
                        # 格式化為 YYYY/M/D (例如 2025/1/4)
                        # %-m 和 %-d 在 Windows 系統可能失效，改用 Python 通用的格式化方式
                        df_melted[col] = df_melted[col].apply(lambda x: f"{x.year}/{x.month}/{x.day}")
                    except:
                        continue # 如果該欄位不是日期格式則跳過

                st.success("🎉 轉換完成！日期已統一格式。")
                st.subheader("3. 轉換結果預覽")
                st.dataframe(df_melted)

                # --- 4. 下載功能 ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_melted.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 下載轉換後的 Excel 檔案",
                    data=output.getvalue(),
                    file_name="formatted_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    except Exception as e:
        st.error(f"❌ 發生錯誤: {e}")