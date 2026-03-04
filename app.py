import streamlit as st
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import os

# --- 1. ตั้งค่าพื้นฐาน (DPI 300) ---
DPI = 300
def cm_to_px(cm): return int((cm / 2.54) * DPI)

TOTAL_W, TOTAL_H = cm_to_px(17.5), cm_to_px(12.7)
SEC_A_H = cm_to_px(5.9)
SEC_B_W = cm_to_px(12.5)
SEC_C_W = cm_to_px(5.0)
SEC_D_H = cm_to_px(0.9)

# --- 2. ฟังก์ชันดึงฟอนต์ (เน้นฟอนต์หนาของระบบ) ---
def get_label_font(size):
    # พยายามหาฟอนต์หนาในระบบ Streamlit Cloud
    paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# --- 3. ฟังก์ชันสร้างป้าย ---
def generate_label(p_name, p_type, pk_num, date_str):
    img = Image.new('RGB', (TOTAL_W, TOTAL_H), color='white')
    draw = ImageDraw.Draw(img)
    
    # วาดกรอบตัด (หนา 10px)
    draw.rectangle([0, 0, TOTAL_W, TOTAL_H], outline="black", width=10)
    
    # ตั้งค่าสีพื้นหลัง
    color_map = {
        "acid": "#FF0000", "กรด": "#FF0000",
        "base": "#0000FF", "ด่าง": "#0000FF",
        "neutral": "#008000", "กลาง": "#008000"
    }
    bg_color = color_map.get(str(p_type).strip().lower(), "gray")
    draw.rectangle([10, 10, TOTAL_W-10, SEC_A_H], fill=bg_color)
    
    # A. ชื่อสินค้า (ProductName) - ฟอนต์ 300 หนา
    f_prod = get_label_font(300)
    draw.text((TOTAL_W/2, SEC_A_H/2), str(p_name).upper(), fill="white", anchor="mm", font=f_prod)

    # B. รหัสภาชนะ - ฟอนต์ 400 หนา
    f_pk = get_label_font(400)
    draw.text((SEC_B_W/2, SEC_A_H + (SEC_A_H/2)), f"PK {pk_num}", fill="black", anchor="mm", font=f_pk)
    
    # C. QR Code
    qr = qrcode.make(f"{str(p_name).replace(' ', '')}PK{pk_num}")
    qr_img = qr.resize((SEC_C_W - 50, SEC_C_W - 50))
    img.paste(qr_img, (SEC_B_W + 25, SEC_A_H + 25))
    
    # D. วันที่ (ชิดขวา) - ฟอนต์ 80
    f_date = get_label_font(80)
    draw.text((TOTAL_W - 50, TOTAL_H - (SEC_D_H/2)), f"Date: {date_str}", fill="black", anchor="rm", font=f_date)
    
    # เส้นตารางภายใน
    draw.line([(0, SEC_A_H), (TOTAL_W, SEC_A_H)], fill="black", width=10)
    draw.line([(SEC_B_W, SEC_A_H), (SEC_B_W, TOTAL_H-SEC_D_H)], fill="black", width=10)
    draw.line([(0, TOTAL_H-SEC_D_H), (TOTAL_W, TOTAL_H-SEC_D_H)], fill="black", width=10)
    
    return img

# --- 4. ส่วนหน้าเว็บ Streamlit ---
st.set_page_config(page_title="Chemical Labeler", layout="centered")
st.title("🏷️ ระบบสร้างป้ายภาชนะสารเคมี")

CSV_FILE = "Products.csv"

# โหลดข้อมูล
def load_csv():
    if os.path.exists(CSV_FILE):
        try:
            return pd.read_csv(CSV_FILE, encoding='utf-8-sig')
        except:
            return pd.read_csv(CSV_FILE, encoding='cp874')
    return pd.DataFrame(columns=["FullName", "ProductName", "Type"])

df = load_csv()
df.columns = df.columns.str.strip()

# --- ปุ่มเพิ่มสินค้า (กลับมาแล้ว) ---
with st.expander("➕ เพิ่มรายชื่อสินค้าใหม่"):
    new_f = st.text_input("ชื่อเต็ม (FullName)")
    new_p = st.text_input("ชื่อย่อบนป้าย (ProductName)")
    new_t = st.selectbox("ประเภทสี", ["กรด", "ด่าง", "กลาง"])
    if st.button("บันทึกข้อมูล"):
        if new_f and new_p:
            new_row = pd.DataFrame([{"FullName": new_f, "ProductName": new_p, "Type": new_t}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
            st.success("บันทึกแล้ว! ระบบกำลังโหลดข้อมูลใหม่...")
            st.rerun()

st.divider()

# --- ส่วนสร้างป้าย ---
if not df.empty:
    target_full = st.selectbox("1. เลือกสินค้าที่ต้องการ", options=df["FullName"].unique())
    row = df[df["FullName"] == target_full].iloc[0]
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        pk_no = st.text_input("2. รหัส PK (3 หลัก)", "000", max_chars=3)
    with col_in2:
        dt_val = st.date_input("3. วันที่", datetime.now())
    
    if st.button("🚀 สร้างตัวอย่างป้าย"):
        result_img = generate_label(row["ProductName"], row["Type"], pk_no, dt_val.strftime("%d/%m/%Y"))
        st.image(result_img, use_container_width=True)
        
        # เตรียมปุ่มดาวน์โหลด
        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        st.download_button("📥 ดาวน์โหลดป้ายเพื่อสั่งพิมพ์", buf.getvalue(), f"Label_{pk_no}.png", "image/png")
else:
    st.warning("ไม่พบข้อมูลใน Products.csv กรุณาเพิ่มสินค้าที่ปุ่มด้านบน")
