import streamlit as st
import os
import re
from groq import Groq
from fpdf import FPDF
from datetime import datetime

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="AI Cover Letter Designer", page_icon="📄", layout="wide")

# --- 2. SECURE API KEY ---
try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception:
    st.error("🔑 GROQ_API_KEY not found. Please add it to your Streamlit App Secrets.")
    st.stop()

# --- 3. SESSION STATE ---
if "letter_body" not in st.session_state:
    st.session_state["letter_body"] = ""
if "form_data" not in st.session_state:
    st.session_state["form_data"] = {}

# --- 4. VALIDATION & EDGE CASE HELPERS ---
def is_text_only(text):
    """Allows only letters and spaces."""
    return bool(re.match(r"^[a-zA-Z\s]*$", text))

def validate_phone(phone):
    """Must contain '+' and exactly 11 digits."""
    digits = re.sub(r"\D", "", phone) # Strip everything but numbers
    return "+" in phone and len(digits) == 11

def clean_for_pdf(text):
    """Replaces 'smart' characters that break FPDF standard fonts."""
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': "-", '\u2014': "-", '\u2026': "..."
    }
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    return text

# --- 5. PDF GENERATION ENGINE ---
def generate_pdf(template, color_name, details, content):
    colors = {
        "Teal": (52, 165, 173), "Forest Green": (34, 139, 34),
        "Navy Blue": (0, 51, 102), "Burgundy": (128, 0, 32), "Charcoal": (54, 69, 79)
    }
    r, g, b = colors.get(color_name, (52, 165, 173))
    
    pdf = FPDF(unit="mm", format="A4")
    pdf.add_page()
    
    # Handle character edge cases
    content = clean_for_pdf(content)
    name = details.get('name', 'Name')

    if "Traditional" in template:
        # --- TEMPLATE: TRADITIONAL ---
        pdf.set_font("times", "B", 24)
        pdf.cell(0, 15, name, ln=True, align="C")
        pdf.set_font("times", "", 10)
        contact_line = f"{details.get('address')} | {details.get('phone')} | {details.get('email')}"
        pdf.cell(0, 5, contact_line, ln=True, align="C")
        pdf.set_draw_color(r, g, b)
        pdf.line(20, 35, 190, 35) # Horizontal Rule
        pdf.ln(20)
        pdf.set_font("times", "", 11)
        pdf.set_x(25)
        pdf.multi_cell(160, 6, content)

    elif "Template 1" in template:
        # --- TEMPLATE: SIDEBAR BOLD ---
        pdf.set_fill_color(r, g, b); pdf.rect(10, 0, 60, 15, 'F')
        pdf.set_xy(10, 20); pdf.set_font("helvetica", "B", 26)
        pdf.set_text_color(0, 0, 0); pdf.cell(60, 15, name.upper(), ln=1)
        pdf.rect(10, 38, 60, 259, 'F')
        pdf.set_xy(15, 45); pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 12); pdf.cell(50, 8, "Personal details", ln=1)
        pdf.line(15, 53, 65, 53)
        pdf.set_font("helvetica", "", 9)
        pdf.set_xy(15, 60); pdf.multi_cell(45, 5, f"Email:\n{details.get('email')}\n\nPhone:\n{details.get('phone')}\n\nAddress:\n{details.get('address')}")
        pdf.set_xy(80, 40); pdf.set_text_color(0, 0, 0); pdf.multi_cell(115, 5, content)
    
    else:
        # --- TEMPLATE: SIDEBAR MINIMAL ---
        pdf.set_fill_color(242, 242, 242); pdf.rect(0, 0, 75, 297, 'F')
        pdf.set_fill_color(r, g, b); pdf.rect(0, 0, 75, 25, 'F')
        pdf.ellipse(-10, 10, 95, 30, 'F')
        pdf.set_xy(5, 12); pdf.set_font("helvetica", "B", 18); pdf.set_text_color(255, 255, 255); pdf.cell(65, 10, name, align="C")
        pdf.set_xy(10, 50); pdf.set_text_color(r, g, b); pdf.set_font("helvetica", "B", 14); pdf.cell(55, 8, "Contact Info", ln=1)
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10); pdf.set_xy(10, 60)
        pdf.multi_cell(55, 6, f"{details.get('email')}\n{details.get('phone')}\n{details.get('address')}")
        pdf.set_xy(85, 15); pdf.multi_cell(110, 5, content)

    return bytes(pdf.output())

# --- 6. THE INPUT FORM ---
st.title("📄 Pro AI Cover Letter Designer")

with st.form(key="robust_generation_form"):
    c1, c2 = st.columns(2)
    with c1:
        u_name = st.text_input("Full Name (Text Only)")
        u_email = st.text_input("Email (Must contain @)")
        u_phone = st.text_input("Phone (Must contain + and 11 digits)", placeholder="+12345678901")
        u_addr = st.text_input("Address (Text Only)")
    with c2:
        u_pos = st.text_input("Target Position (Text Only)")
        u_comp = st.text_input("Company Name (Text Only)")
        u_skls = st.text_area("Key Skills (Text Only)")
    
    st.subheader("Design & Style")
    t_style = st.selectbox("Template Style", ["Traditional - Classic Times", "Template 1 - Sidebar Bold", "Template 2 - Sidebar Minimal"])
    t_color = st.selectbox("Color Theme", ["Teal", "Forest Green", "Navy Blue", "Burgundy", "Charcoal"])
    
    submit = st.form_submit_button("Generate & Validate", type="primary")

# --- 7. LOGIC WITH EDGE CASING ---
if submit:
    # Validation Logic
    error_found = False
    
    if not all([u_name, u_email, u_phone, u_addr, u_pos, u_comp, u_skls]):
        st.error("All fields are required.")
        error_found = True
    elif not is_text_only(u_name):
        st.error("Full Name must only contain letters.")
        error_found = True
    elif "@" not in u_email:
        st.error("Invalid Email: Missing '@' symbol.")
        error_found = True
    elif not validate_phone(u_phone):
        st.error("Phone must contain '+' and exactly 11 digits.")
        error_found = True
    elif not all(is_text_only(x) for x in [u_pos, u_comp, u_addr]):
        st.error("Position, Company, and Address must be text only.")
        error_found = True

    if not error_found:
        with st.spinner("AI is crafting your letter..."):
            try:
                prompt = f"Write a professional cover letter for {u_name} applying for {u_pos} at {u_comp}. Skills: {u_skls}."
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.session_state["letter_body"] = f"Hiring Manager\n{u_comp}\n\n{datetime.now().strftime('%B %d, %Y')}\n\n{response.choices[0].message.content}"
                st.session_state["form_data"] = {"name": u_name, "email": u_email, "phone": u_phone, "address": u_addr, "tmpl": t_style, "clr": t_color}
            except Exception as e:
                st.error(f"Groq API Error: {str(e)}")

# --- 8. REVIEW & DOWNLOAD ---
if st.session_state.get("letter_body"):
    st.divider()
    final_text = st.text_area("Final Edit:", value=st.session_state["letter_body"], height=350)
    
    pdf_out = generate_pdf(
        st.session_state["form_data"]["tmpl"], 
        st.session_state["form_data"]["clr"], 
        st.session_state["form_data"], 
        final_text
    )
    
    st.download_button(
        label="Download Professional PDF", 
        data=pdf_out, 
        file_name=f"{u_name.replace(' ', '_')}_CoverLetter.pdf", 
        mime="application/pdf"
    )
