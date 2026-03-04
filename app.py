import streamlit as st
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import os

# --- 1. ตั้งค่าคงที่ (DPI 300) ---
DPI = 300
def cm_to_px(cm): return int((cm / 2.54) * DPI)

TOTAL_W, TOTAL_H = cm_to_px(17.5), cm_to_px(12.7)
SEC_A_H = cm_to_px(5.9)
SEC_B_W = cm_to_px(12.5)
SEC_C_W = cm_to_px(5.0)
SEC_D_H = cm_to_px(0.9)

# --- 2. ฟังก์ชันโหลดฟอนต์ที่เสถียรที่สุด ---
def get_safe_font(size):
    paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# --- 3. ฟังก์ชันสร้างรูปป้าย ---
def generate_label(p_name, p_type, pk_num, date_str):
    img = Image.new('RGB', (TOTAL_W, TOTAL_H), color='white')
    draw = ImageDraw.Draw(img)
    
    # วาดกรอบตัด (หนาพิเศษ)
    draw.rectangle([0, 0, TOTAL_W, TOTAL_H], outline="black", width=10)
    
    # ตั้งสีตามประเภท (เปลี่ยนเป็น Eng)
    color_map = {
        "acid": "#FF0000",   # กรด -> Red
        "base": "#0000FF",   # ด่าง -> Blue
        "neutral": "#008000" # กลาง -> Green
    }
    # รองรับทั้งไทยและอังกฤษจากไฟล์เดิม
    type_clean = str(p_type).strip()
    if type_clean == "กรด": type_clean = "acid"
    elif type_clean == "ด่าง": type_clean = "base"
    elif type_clean == "กลาง": type_clean = "neutral"
    
    bg_color = color_map.get(type_clean.lower(), "gray")
    draw.rectangle([10, 10, TOTAL_W-10, SEC_A_H], fill=bg_color)
    
    # เขียนชื่อสินค้า (ProductName)
    f_prod = get_safe_font(300)
    draw.text((TOTAL_W/2, SEC_A_H/2), str(p_name).upper(), fill="white", anchor="mm", font=f_prod)

    # เขียนรหัส PK
    f_pk = get_safe_font(400)
    draw.text((SEC_B_W/2, SEC_A_H + (SEC_A_H/2)), f"PK {pk_num}", fill="black", anchor="mm", font=f_pk)
    
    # QR Code
    qr = qrcode.make(f"{str(p_name).replace(' ', '')}PK{pk_num}")
    qr_img = qr.resize((SEC_C_W - 50, SEC_C_W - 50))
    img.paste(qr_img, (SEC_B_W + 25, SEC_A_H + 25))
    
    # วันที่ (ปรับขนาดฟอนต์ให้ใหญ่ขึ้น)
    f_date = get_safe_font(80)
    draw.text((TOTAL_W - 50, TOTAL_H - (SEC_D_H/2)), f"Date: {date_str}", fill="black", anchor="rm", font=f_date)
    
    # เส้นแบ่งโครงสร้าง
    draw.line([(0, SEC_A_H), (TOTAL_W, SEC_A_H)], fill="black", width=10)
    draw.line([(SEC_B_W, SEC_A_H), (SEC_B_W, TOTAL_H-SEC_D_H)], fill="black", width=10)
    draw.line([(0, TOTAL_H-SEC_D_H), (TOTAL_W, TOTAL_H-SEC_D_H)], fill="black", width=10)
    
    return img

# --- 4. ส่วนหน้าเว็บ Streamlit ---
st.set_page_config(page_title="Easy Label", layout="centered")
st.title("🏷️ เครื่องมือสร้างป้ายสินค้า (Simple Ver.)")

CSV_FILE = "Products.csv"

# โหลดข้อมูลสินค้า
@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        try:
            return pd.read_csv(CSV_FILE, encoding='utf-8-sig')
        except:
            return pd.read_csv(CSV_FILE, encoding='cp874')
    return pd.DataFrame(columns=["FullName", "ProductName", "Type"])

df = load_data()
df.columns = df.columns.str.strip()

# --- เมนูเพิ่มสินค้า (กู้คืนมาแล้ว) ---
with st.expander("➕ เพิ่มสินค้าใหม่ (Add New Product)"):
    col1, col2 = st.columns(2)
    with col1:
        new_f = st.text_input("FullName (ชื่ออ้างอิง)")
        new_p = st.text_input("ProductName (ชื่อบนป้าย)")
    with col2:
        new_t = st.selectbox("Type", ["acid", "base", "neutral"])
    
    if st.button("บันทึกลงฐานข้อมูล"):
        if new_f and new_p:
            new_row = pd.DataFrame([{"FullName": new_f, "ProductName": new_p, "Type": new_t}])
            new_df = pd.concat([df, new_row], ignore_index=True)
            new_df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
            st.success("บันทึกสำเร็จ! กรุณารีเฟรชหน้าเว็บ")
            st.cache_data.clear()
            st.rerun()

st.divider()

# --- ส่วนสร้างป้าย ---
if not df.empty:
    target_full = st.selectbox("1. เลือกสินค้า", options=df["FullName"].unique())
    row = df[df["FullName"] == target_full].iloc[0]
    
    pk_no = st.text_input("2. รหัส PK", "000", max_chars=3)
    dt_now = st.date_input("3. วันที่", datetime.now())
    
    if st.button("🚀 สร้างป้ายและดูตัวอย่าง"):
        result = generate_label(row["ProductName"], row["Type"], pk_no, dt_now.strftime("%d/%m/%Y"))
        st.image(result, use_container_width=True)
        
        # ปุ่ม Download
        buf = io.BytesIO()
        result.save(buf, format="PNG")
        st.download_button("📥 ดาวน์โหลดป้าย (PNG)", buf.getvalue(), f"Label_{pk_no}.png", "image/png")
else:
    st.warning("ยังไม่มีข้อมูลสินค้าในไฟล์ Products.csv")
