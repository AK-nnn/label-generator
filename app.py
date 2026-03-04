import streamlit as st
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import os

# --- Config ขนาด (300 DPI) ---
DPI = 300
def cm_to_px(cm): return int((cm / 2.54) * DPI)
TOTAL_W, TOTAL_H = cm_to_px(17.5), cm_to_px(12.7)
SEC_A_H, SEC_B_W, SEC_C_W, SEC_D_H = cm_to_px(5.9), cm_to_px(12.5), cm_to_px(5.0), cm_to_px(0.9)

def generate_label(display_name, p_type, pk_num, date_str):
    img = Image.new('RGB', (TOTAL_W, TOTAL_H), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, TOTAL_W-1, TOTAL_H-1], outline="black", width=5)
    
    color_map = {"กรด": "#FF0000", "ด่าง": "#0000FF", "กลาง": "#008000"}
    bg_color = color_map.get(str(p_type).strip(), "gray")
    draw.rectangle([5, 5, TOTAL_W-5, SEC_A_H], fill=bg_color)
    
    font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    
    def get_font(text, max_w, max_h, start_size):
        size = start_size
        f = ImageFont.load_default()
        while size > 10:
            try:
                if os.path.exists(font_path): f = ImageFont.truetype(font_path, size)
                else: break
            except: break
            bbox = draw.textbbox((0,0), text, font=f)
            if (bbox[2]-bbox[0]) <= max_w-60: break
            size -= 10
        return f

    draw.text((TOTAL_W/2, SEC_A_H/2), str(display_name).upper(), fill="white", anchor="mm", font=get_font(str(display_name), TOTAL_W, SEC_A_H, 350))
    draw.text((SEC_B_W/2, SEC_A_H + (SEC_A_H/2)), f"PK {pk_num}", fill="black", anchor="mm", font=get_font(f"PK {pk_num}", SEC_B_W, SEC_A_H, 350))
    
    qr_data = f"{str(display_name).replace(' ', '')} PK{pk_num}"
    qr = qrcode.make(qr_data)
    qr_img = qr.resize((SEC_C_W - 60, SEC_C_W - 60))
    img.paste(qr_img, (SEC_B_W + 30, SEC_A_H + 30))
    
    draw.text((TOTAL_W - 60, TOTAL_H - (SEC_D_H/2)), f"Date: {date_str}", fill="black", anchor="rm")
    
    draw.line([(0, SEC_A_H), (TOTAL_W, SEC_A_H)], fill="black", width=5)
    draw.line([(SEC_B_W, SEC_A_H), (SEC_B_W, TOTAL_H-SEC_D_H)], fill="black", width=5)
    draw.line([(0, TOTAL_H-SEC_D_H), (TOTAL_W, TOTAL_H-SEC_D_H)], fill="black", width=5)
    return img

# --- UI ---
st.set_page_config(page_title="Generator ป้ายภาชนะ", layout="centered")
st.title("📦 ระบบสร้างป้ายภาชนะสินค้า")

# --- ส่วนการค้นหาไฟล์แบบยืดหยุ่น ---
files_in_dir = os.listdir('.')
csv_files = [f for f in files_in_dir if f.lower() == 'products.csv']

if csv_files:
    CSV_FILE = csv_files[0]
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
    except:
        df = pd.read_csv(CSV_FILE, encoding='cp874')
    
    df.columns = df.columns.str.strip()
    
    with st.expander("➕ เพิ่มสินค้าใหม่"):
        new_fn = st.text_input("FullName")
        new_pn = st.text_input("ProductName")
        new_t = st.selectbox("ประเภท", ["กรด", "ด่าง", "กลาง"])
        if st.button("บันทึก"):
            new_row = pd.DataFrame([{"FullName": new_fn, "ProductName": new_pn, "Type": new_t}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
            st.success("บันทึกแล้ว!")
            st.rerun()

    st.divider()

    # ตรวจสอบว่ามีคอลัมน์ครบไหม
    if "FullName" in df.columns:
        full_name_list = sorted(df["FullName"].dropna().unique().tolist())
        selected_full = st.selectbox("1. ค้นหาชื่อสินค้า (FullName)", options=["--- โปรดเลือกสินค้า ---"] + full_name_list)
        
        if selected_full != "--- โปรดเลือกสินค้า ---":
            row = df[df["FullName"] == selected_full].iloc[0]
            prod_name = row["ProductName"]
            prod_type = row["Type"]
            
            st.info(f"🏷️ ชื่อบนป้าย: **{prod_name}** | 🎨 ประเภท: **{prod_type}**")
            pk_val = st.text_input("2. รหัสภาชนะ 3 หลัก", "000", max_chars=3)
            date_val = st.date_input("3. วันที่", datetime.now())

            if st.button("🚀 สร้างป้าย"):
                res = generate_label(prod_name, prod_type, pk_val, date_val.strftime("%d/%m/%Y"))
                st.image(res)
                buf = io.BytesIO()
                res.save(buf, format="PNG")
                st.download_button("📥 Download PNG", buf.getvalue(), f"Label_{pk_val}.png")
    else:
        st.error(f"ไฟล์พบแล้วแต่หัวตารางผิด! หัวตารางที่มีคือ: {list(df.columns)}")
else:
    st.error("❌ ไม่พบไฟล์ Products.csv ใน GitHub ของคุณ กรุณาอัปโหลดไฟล์ไปที่หน้าแรกของ Repository")
    st.write("ไฟล์ที่พบในระบบตอนนี้คือ:", files_in_dir)
