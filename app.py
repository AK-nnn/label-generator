import streamlit as st
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import os

# =========================
# 1. ตั้งค่าพื้นฐาน
# =========================

DPI = 300
def cm_to_px(cm): 
    return int((cm / 2.54) * DPI)

TOTAL_W, TOTAL_H = cm_to_px(17.5), cm_to_px(12.7)
SEC_A_H = cm_to_px(5.9)
SEC_B_W = cm_to_px(12.5)
SEC_C_W = cm_to_px(5.0)
SEC_D_H = cm_to_px(0.9)

FONT_PATH = "fonts/NotoSansThai-Bold.ttf"

# =========================
# 2. ฟังก์ชันคำนวณฟอนต์อัตโนมัติ
# =========================

def auto_fit_font(draw, text, max_width, max_height):
    size = 500  # ขนาดเริ่มต้นใหญ่ ๆ
    while size > 10:
        font = ImageFont.truetype(FONT_PATH, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= max_width and h <= max_height:
            return font
        size -= 10
    return ImageFont.truetype(FONT_PATH, 50)

# =========================
# 3. ฟังก์ชันสร้างป้าย
# =========================

def generate_label(p_name, p_type, pk_num, date_str):
    img = Image.new('RGB', (TOTAL_W, TOTAL_H), color='white')
    draw = ImageDraw.Draw(img)

    # กรอบตัด
    draw.rectangle([0, 0, TOTAL_W, TOTAL_H], outline="black", width=10)

    # สีพื้น
    color_map = {
        "acid": "#FF0000", "กรด": "#FF0000",
        "base": "#0000FF", "ด่าง": "#0000FF",
        "neutral": "#008000", "กลาง": "#008000"
    }
    bg_color = color_map.get(str(p_type).strip().lower(), "gray")
    draw.rectangle([10, 10, TOTAL_W-10, SEC_A_H], fill=bg_color)

    # =========================
    # A. ชื่อสินค้า (Auto Fit)
    # =========================
    margin = 40
    max_w = TOTAL_W - (margin * 2)
    max_h = SEC_A_H - (margin * 2)

    product_font = auto_fit_font(draw, str(p_name).upper(), max_w, max_h)

    draw.text(
        (TOTAL_W/2, SEC_A_H/2),
        str(p_name).upper(),
        fill="white",
        anchor="mm",
        font=product_font
    )

    # =========================
    # B. รหัสภาชนะ (ใหญ่พอดีช่อง)
    # =========================
    pk_text = f"PK {pk_num}"
    max_w_pk = SEC_B_W - 40
    max_h_pk = (TOTAL_H - SEC_A_H - SEC_D_H) - 40

    pk_font = auto_fit_font(draw, pk_text, max_w_pk, max_h_pk)

    draw.text(
        (SEC_B_W/2, SEC_A_H + ((TOTAL_H-SEC_A_H-SEC_D_H)/2)),
        pk_text,
        fill="black",
        anchor="mm",
        font=pk_font
    )

    # =========================
    # C. QR Code
    # =========================
    qr = qrcode.make(f"{str(p_name).replace(' ', '')}PK{pk_num}")
    qr_size = SEC_C_W - 80
    qr_img = qr.resize((qr_size, qr_size))
    img.paste(qr_img, (SEC_B_W + 40, SEC_A_H + 40))

    # =========================
    # D. วันที่
    # =========================
    date_font = ImageFont.truetype(FONT_PATH, 120)

    draw.text(
        (TOTAL_W - 40, TOTAL_H - (SEC_D_H/2)),
        f"Date: {date_str}",
        fill="black",
        anchor="rm",
        font=date_font
    )

    # เส้นแบ่ง
    draw.line([(0, SEC_A_H), (TOTAL_W, SEC_A_H)], fill="black", width=10)
    draw.line([(SEC_B_W, SEC_A_H), (SEC_B_W, TOTAL_H-SEC_D_H)], fill="black", width=10)
    draw.line([(0, TOTAL_H-SEC_D_H), (TOTAL_W, TOTAL_H-SEC_D_H)], fill="black", width=10)

    return img

# =========================
# 4. Streamlit UI
# =========================

st.set_page_config(page_title="Chemical Labeler", layout="centered")
st.title("🏷️ ระบบสร้างป้ายภาชนะสารเคมี")

CSV_FILE = "Products.csv"

def load_csv():
    if os.path.exists(CSV_FILE):
        try:
            return pd.read_csv(CSV_FILE, encoding='utf-8-sig')
        except:
            return pd.read_csv(CSV_FILE, encoding='cp874')
    return pd.DataFrame(columns=["FullName", "ProductName", "Type"])

df = load_csv()
df.columns = df.columns.str.strip()

with st.expander("➕ เพิ่มรายชื่อสินค้าใหม่"):
    new_f = st.text_input("ชื่อเต็ม (FullName)")
    new_p = st.text_input("ชื่อย่อบนป้าย (ProductName)")
    new_t = st.selectbox("ประเภทสี", ["กรด", "ด่าง", "กลาง"])
    if st.button("บันทึกข้อมูล"):
        if new_f and new_p:
            new_row = pd.DataFrame([{
                "FullName": new_f,
                "ProductName": new_p,
                "Type": new_t
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
            st.success("บันทึกแล้ว! กำลังโหลดใหม่...")
            st.rerun()

st.divider()

if not df.empty:
    target_full = st.selectbox("1. เลือกสินค้า", options=df["FullName"].unique())
    row = df[df["FullName"] == target_full].iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        pk_no = st.text_input("2. รหัส PK (3 หลัก)", "001", max_chars=3)
    with col2:
        dt_val = st.date_input("3. วันที่", datetime.now())

    if st.button("🚀 สร้างป้าย"):
        result_img = generate_label(
            row["ProductName"],
            row["Type"],
            pk_no,
            dt_val.strftime("%d/%m/%Y")
        )

        st.image(result_img, width=900)

        buf = io.BytesIO()
        result_img.save(buf, format="PNG", dpi=(300,300))

        st.download_button(
            "📥 ดาวน์โหลดไฟล์สำหรับพิมพ์",
            buf.getvalue(),
            f"Label_{pk_no}.png",
            "image/png"
        )
else:
    st.warning("ไม่พบข้อมูลใน Products.csv กรุณาเพิ่มสินค้า")
