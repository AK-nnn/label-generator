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

# --- Function: สร้างป้าย ---
def generate_label(name, p_type, pk_num, date_str):
    img = Image.new('RGB', (TOTAL_W, TOTAL_H), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, TOTAL_W-1, TOTAL_H-1], outline="black", width=5)
    
    color_map = {"acid": "#FF0000", "base": "#0000FF", "neutral": "#008000"}
    draw.rectangle([5, 5, TOTAL_W-5, SEC_A_H], fill=color_map.get(p_type, "gray"))
    
    # พยายามใช้ Font มาตรฐานของระบบ
    font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    
    def get_font(text, max_w, max_h, start_size):
        size = start_size
        while size > 10:
            try:
                f = ImageFont.truetype(font_path, size)
            except:
                f = ImageFont.load_default()
            bbox = draw.textbbox((0,0), text, font=f)
            if (bbox[2]-bbox[0]) <= max_w-60: break
            size -= 10
        return f

    # วาดข้อความ
    draw.text((TOTAL_W/2, SEC_A_H/2), name.upper(), fill="white", anchor="mm", font=get_font(name, TOTAL_W, SEC_A_H, 350))
    draw.text((SEC_B_W/2, SEC_A_H + (SEC_A_H/2)), f"PK {pk_num}", fill="black", anchor="mm", font=get_font(f"PK {pk_num}", SEC_B_W, SEC_A_H, 350))
    
    # QR Code
    qr = qrcode.QRCode(box_size=1, border=1)
    qr.add_data(f"{name.replace(' ', '')} PK{pk_num}")
    qr.make(fit=True)
    qr_img = qr.make_image().resize((SEC_C_W - 60, SEC_C_W - 60))
    img.paste(qr_img, (SEC_B_W + 30, SEC_A_H + 30))
    
    # วันที่
    draw.text((TOTAL_W - 60, TOTAL_H - (SEC_D_H/2)), f"Date: {date_str}", fill="black", anchor="rm")
    
    # เส้นแบ่ง
    draw.line([(0, SEC_A_H), (TOTAL_W, SEC_A_H)], fill="black", width=5)
    draw.line([(SEC_B_W, SEC_A_H), (SEC_B_W, TOTAL_H-SEC_D_H)], fill="black", width=5)
    draw.line([(0, TOTAL_H-SEC_D_H), (TOTAL_W, TOTAL_H-SEC_D_H)], fill="black", width=5)
    return img

# --- UI ส่วนหน้าเว็บ ---
st.set_page_config(page_title="Label Generator", layout="centered")
st.title("🏷️ เครื่องมือสร้างป้ายภาชนะ")

# จัดการฐานข้อมูลสินค้า
CSV_FILE = "products.csv"
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=["ProductName", "Type"]).to_csv(CSV_FILE, index=False)

df = pd.read_csv(CSV_FILE)

# เมนูเพิ่มสินค้า
with st.expander("➕ เพิ่มสินค้าใหม่เข้าฐานข้อมูล"):
    new_n = st.text_input("ระบุชื่อสินค้าใหม่")
    new_t = st.selectbox("ระบุประเภท", ["acid", "base", "neutral"])
    if st.button("บันทึกสินค้าใหม่"):
        if new_n:
            new_row = pd.DataFrame([{"ProductName": new_n, "Type": new_t}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.success(f"บันทึก {new_n} เรียบร้อยแล้ว!")
            st.rerun()

# ฟอร์มสร้างป้าย
st.divider()
p_list = df["ProductName"].tolist()
if p_list:
    target_name = st.selectbox("1. เลือกสินค้าจากรายการ", p_list)
    target_type = df[df["ProductName"] == target_name]["Type"].values[0]
    pk_val = st.text_input("2. ระบุเลขรหัสภาชนะ (เช่น 014)", "000", max_chars=3)
    date_val = st.date_input("3. เลือกวันที่", datetime.now())

    if st.button("🚀 สร้างป้าย (Generate)"):
        res = generate_label(target_name, target_type, pk_val, date_val.strftime("%d/%m/%Y"))
        st.image(res, caption="ตัวอย่างป้ายที่จะได้รับ", use_container_width=True)
        
        # เตรียมไฟล์สำหรับ Download
        buf = io.BytesIO()
        res.save(buf, format="PNG")
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ป้าย (PNG)",
            data=buf.getvalue(),
            file_name=f"Label_{target_name}_{pk_val}.png",
            mime="image/png"
        )
else:
    st.warning("ยังไม่มีข้อมูลสินค้าในระบบ กรุณาเพิ่มสินค้าใหม่ที่เมนูด้านบน")