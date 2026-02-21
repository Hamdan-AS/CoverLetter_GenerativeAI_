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
    """
    Validates: Starts with '+', Country Code: 1-3 digits, Subscriber: Max 12 digits.
    """
    if not phone.startswith('+'):
        return False, "Phone must start with '+'"
    
    digits = re.sub(r"\D", "", phone)
    
    if len(digits) < 2 or len(digits) > 15:
        return False, "Phone digits must be between 2 and 15 total."
    
    return True, ""

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
    
    content = clean_for_pdf(content)
    name = details.get('name', 'Name')

    if "Traditional" in template:
        pdf.set_font("times", "B", 24)
        pdf.cell(0, 15, name, ln=True, align="C")
        pdf.set_font("times", "", 10)
        pdf.cell(0, 5, f"{details.get('address')} | {details.get('phone')} | {details.get('email')}", ln=True, align="C")
        
        pdf.set_draw_color(r, g, b)
        pdf.line(20, 35, 190, 35)
        
        pdf.ln(15) 
        pdf.set_font("times", "", 11)
        pdf.set_left_margin(25)
        pdf.set_right_margin(25)
        pdf.multi_cell(0, 6, content) 

    elif "Template 1" in template:
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
        # --- TEMPLATE: SIDEBAR MINIMAL (IMPROVED) ---
        pdf.set_fill_color(242, 242, 242); pdf.rect(0, 0, 75, 297, 'F')
        pdf.set_fill_color(r, g, b); pdf.rect(0, 0, 75, 25, 'F')
        pdf.ellipse(-10, 10, 95, 30, 'F')
    
        pdf.set_xy(5, 12); pdf.set_font("helvetica", "B", 18); pdf.set_text_color(255, 255, 255)
        pdf.cell(65, 10, name, align="C")
    
        pdf.set_xy(10, 50); pdf.set_text_color(r, g, b); pdf.set_font("helvetica", "B", 12)
        pdf.cell(55, 8, "CONTACT DETAILS", ln=1)
    
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10); pdf.set_xy(10, 60)
        contact_info = (
            f"Email: {details.get('email')}\n\n"
            f"Phone: {details.get('phone')}\n\n"
            f"Address: {details.get('address')}")
        pdf.multi_cell(55, 6, contact_info) 
    
        pdf.set_xy(85, 15); pdf.multi_cell(110, 5, content)

    # FIXED: return statement must be outside the if/else blocks to work for all templates
    return bytes(pdf.output())

# --- 6. THE INPUT FORM ---
st.title("📄 Pro AI Cover Letter Designer")

with st.form(key="robust_generation_form"):
    c1, c2 = st.columns(2)
    with c1:
        u_name = st.text_input("Full Name (Text Only)")
        u_email = st.text_input("Email (Must contain @)")
        u_phone = st.text_input("Phone Number", placeholder="For EG: +92 7911123456")
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
    
    phone_valid, phone_err = validate_phone(u_phone)
    if not phone_valid:
        st.error(phone_err)
        error_found = True
    elif not all(is_text_only(x) for x in [u_pos, u_comp, u_addr]):
        st.error("Position, Company, and Address must be text only.")
        error_found = True

    if not error_found:
        with st.spinner("AI is crafting your letter..."):
            try:
                prompt = (
                    f"Write a professional cover letter for {u_name} for the {u_pos} position at {u_comp}. "
                    f"Focus on these skills: {u_skls}. "
                    "STRICT INSTRUCTION: Provide ONLY the body text. "
                    "DO NOT include a date, addresses, or any square brackets like [Today's Date] or [City, State]. "
                    "Start directly with 'Dear Hiring Manager,' and end with 'Sincerely,' followed by the name."
                )
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.session_state["letter_body"] = response.choices[0].message.content
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
