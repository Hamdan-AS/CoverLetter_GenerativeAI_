import streamlit as st
import os
from groq import Groq
from fpdf import FPDF
from datetime import datetime

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="AI Cover Letter Designer", page_icon="📄", layout="wide")

# --- 2. SECURE API KEY (TOML via st.secrets) ---
try:
    # This pulls from the TOML secrets you set in the Streamlit Dashboard
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception:
    st.error("🔑 GROQ_API_KEY not found. Please add it to your Streamlit App Secrets in the dashboard.")
    st.stop()

# --- 3. SESSION STATE INITIALIZATION ---
if "letter_body" not in st.session_state:
    st.session_state["letter_body"] = ""
if "form_data" not in st.session_state:
    st.session_state["form_data"] = {}

# --- 4. PDF GENERATION ENGINE ---
def generate_pdf(template, color_name, details, content):
    colors = {
        "Teal": (52, 165, 173), "Forest Green": (34, 139, 34),
        "Navy Blue": (0, 51, 102), "Burgundy": (128, 0, 32), "Charcoal": (54, 69, 79)
    }
    r, g, b = colors.get(color_name, (52, 165, 173))
    
    pdf = FPDF(unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    
    name = details.get('name', 'Name')
    
    if "Template 1" in template:
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
        pdf.set_fill_color(242, 242, 242); pdf.rect(0, 0, 75, 297, 'F')
        pdf.set_fill_color(r, g, b); pdf.rect(0, 0, 75, 25, 'F')
        pdf.ellipse(-10, 10, 95, 30, 'F')
        pdf.set_xy(5, 12); pdf.set_font("helvetica", "B", 18); pdf.set_text_color(255, 255, 255); pdf.cell(65, 10, name, align="C")
        pdf.set_xy(10, 50); pdf.set_text_color(r, g, b); pdf.set_font("helvetica", "B", 14); pdf.cell(55, 8, "Contact Info", ln=1)
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10); pdf.set_xy(10, 60)
        pdf.multi_cell(55, 6, f"{details.get('email')}\n{details.get('phone')}\n{details.get('address')}")
        pdf.set_xy(85, 15); pdf.multi_cell(110, 5, content)

    return bytes(pdf.output())

# --- 5. THE INPUT FORM ---
st.title("📄 Professional AI Cover Letter Designer")

# UNIQUE KEY "final_version_form" prevents the Duplicate Form error
with st.form(key="final_version_form"):
    c1, c2 = st.columns(2)
    with c1:
        u_name = st.text_input("Full Name", "Jane Fitz")
        u_email = st.text_input("Email", "jane@example.com")
        u_phone = st.text_input("Phone", "(222) 345-6789")
        u_addr = st.text_input("Address", "Scranton, PA")
    with c2:
        u_pos = st.text_input("Target Position")
        u_comp = st.text_input("Company Name")
        u_skls = st.text_area("Key Skills & Experience")
    
    st.subheader("Design & Style")
    t_style = st.selectbox("Template Style", ["Template 1 - Sidebar Bold", "Template 2 - Sidebar Minimal"])
    t_color = st.selectbox("Color Theme", ["Teal", "Forest Green", "Navy Blue", "Burgundy", "Charcoal"])
    
    submit = st.form_submit_button("Generate Professional Letter", type="primary")

# --- 6. GENERATION LOGIC ---
if submit:
    if not u_pos or not u_comp:
        st.warning("Please provide the Position and Company.")
    else:
        with st.spinner("Llama 3.3 is crafting your letter..."):
            try:
                # UPDATED MODEL: llama-3.3-70b-versatile
                prompt = f"Write a professional cover letter for {u_name} applying for {u_pos} at {u_comp}. Highlight these skills: {u_skls}."
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Store the result
                st.session_state["letter_body"] = f"Hiring Manager\n{u_comp}\n\n{datetime.now().strftime('%B %d, %Y')}\n\n{response.choices[0].message.content}"
                st.session_state["form_data"] = {"name": u_name, "email": u_email, "phone": u_phone, "address": u_addr, "tmpl": t_style, "clr": t_color}
                
            except Exception as e:
                st.error(f"Groq API Error: {str(e)}")

# --- 7. REVIEW & DOWNLOAD ---
if st.session_state.get("letter_body"):
    st.divider()
    final_text = st.text_area("Edit your letter:", value=st.session_state["letter_body"], height=350)
    
    pdf_out = generate_pdf(
        st.session_state["form_data"]["tmpl"], 
        st.session_state["form_data"]["clr"], 
        st.session_state["form_data"], 
        final_text
    )
    
    st.download_button(
        label="Download Professional PDF", 
        data=pdf_out, 
        file_name=f"{u_name.replace(' ', '_')}_Cover_Letter.pdf", 
        mime="application/pdf",
        type="primary"
    )
