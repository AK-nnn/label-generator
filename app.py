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
    
    # วาดกรอบนอกสุด (เส้นหนาขึ้นเพื่อให้เห็นชัดตอนตัด)
    draw.rectangle([0, 0, TOTAL_W-1, TOTAL_H-1], outline="black", width=8)
    
    # Mapping สี
    color_map = {"กรด": "#FF0000", "ด่าง": "#0000FF", "กลาง": "#008000"}
    bg_color = color_map.get(str(p_type).strip(), "gray")
    draw.rectangle([8, 8, TOTAL_W-8, SEC_A_H], fill=bg_color)
    
    font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    
    def get_font(text, max_w, max_h, start_size):
        size = start_size
        if not os.path.exists(font_path):
            return ImageFont.load_default()
        
        f = ImageFont.truetype(font_path, size)
        while size > 20:
            bbox = draw.textbbox((0,0), text, font=f)
            w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            # ปรับให้เหลือ Margin แค่ 30 พิกเซล (เพื่อให้ฟอนต์ขยายได้เกือบเต็มพื้นที่)
            if w <= max_w-30 and h <= max_h-10: 
                break
            size -= 5
            f = ImageFont.truetype(font_path, size)
        return f

    # A. ProductName (ขยายให้สะใจ เริ่มที่ 600)
    f_prod = get_font(str(display_name).upper(), TOTAL_W, SEC_A_H, 600)
    draw.text((TOTAL_W/2, SEC_A_H/2), str(display_name).upper(), fill="white", anchor="mm", font=f_prod)

    # B. PK Code (ขยายให้สะใจ เริ่มที่ 800)
    f_pk = get_font(f"PK {pk_num}", SEC_B_W, SEC_A_H, 800)
    draw.text((SEC_B_W/2, SEC_A_H + (SEC_A_H/2)), f"PK {pk_num}", fill="black", anchor="mm", font=f_pk)
    
    # C. QR Code
    qr_data = f"{str(display_name).replace(' ', '')} PK{pk_num}"
    qr = qrcode.QRCode(box_size=1, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    # ขยาย QR ให้ใหญ่ขึ้นอีกนิด
    qr_img = qr.make_image().resize((SEC_C_W - 20, SEC_C_W - 20))
    img.paste(qr_img, (SEC_B_W + 10, SEC_A_H + 10))
    
    # D. Date (ขยายเป็นขนาด 100)
    try:
        f_date = ImageFont.truetype(font_path, 100)
    except:
        f_date = ImageFont.load_default()
    
    draw.text((TOTAL_W - 30, TOTAL_H - (SEC_D_H/2)), f"Date: {date_str}", fill="black", anchor="rm", font=f_date)
    
    # วาดเส้นแบ่งโครงสร้าง (หนา 8 พิกเซล)
    draw.line([(0, SEC_A_H), (TOTAL_W, SEC_A_H)], fill="black", width=8)
    draw.line([(SEC_B_W, SEC_A_H), (SEC_B_W, TOTAL_H-SEC_D_H)], fill="black", width=8)
    draw.line([(0, TOTAL_H-SEC_D_H), (TOTAL_W, TOTAL_H-SEC_D_H)], fill="black", width=8)
    return img

# --- ส่วน UI เหมือนเดิม ---
st.set_page_config(page_title="Generator ป้ายภาชนะ", layout="centered")
st.title("📦 ระบบสร้างป้ายภาชนะสินค้า")

files = [f for f in os.listdir('.') if f.lower() == 'products.csv']

if files:
    CSV_FILE = files[0]
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
    except:
        df = pd.read_csv(CSV_FILE, encoding='cp874')
    
    df.columns = df.columns.str.strip()
    
    if "FullName" in df.columns:
        full_names = sorted(df["FullName"].dropna().unique().tolist())
        selected = st.selectbox("เลือกสินค้า (FullName)", options=["--- กรุณาเลือก ---"] + full_names)
        
        if selected != "--- กรุณาเลือก ---":
            row = df[df["FullName"] == selected].iloc[0]
            p_name = row["ProductName"]
            p_type = row["Type"]
            
            st.success(f"ชื่อบนป้าย: {p_name} | ประเภท: {p_type}")
            pk = st.text_input("รหัสภาชนะ 3 หลัก", "000", max_chars=3)
            dt = st.date_input("วันที่", datetime.now())

            if st.button("🚀 สร้างป้าย"):
                res = generate_label(p_name, p_type, pk, dt.strftime("%d/%m/%Y"))
                st.image(res, use_container_width=True)
                
                buf = io.BytesIO()
                res.save(buf, format="PNG")
                st.download_button("📥 ดาวน์โหลดป้าย", buf.getvalue(), f"Label_{pk}.png")
else:
    st.error("ไม่พบไฟล์ Products.csv")
