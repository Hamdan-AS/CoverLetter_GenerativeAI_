import streamlit as st
import os
from groq import Groq
from fpdf import FPDF
from datetime import datetime

# --- INITIALIZATION ---
st.set_page_config(page_title="AI Cover Letter Designer", page_icon="📄", layout="wide")

# This prevents the "KeyError" during the initial background boot-up
if "full_letter" not in st.session_state:
    st.session_state["full_letter"] = ""
if "data" not in st.session_state:
    st.session_state["data"] = {}

# Access the API key securely from the environment
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    st.error("🔑 API Key not found. Add 'GROQ_API_KEY' to your Secrets/Environment Variables.")
    st.stop()

client = Groq(api_key=api_key)

# --- PDF ENGINE ---
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
        # Style 1: Bold Sidebar
        pdf.set_fill_color(r, g, b)
        pdf.rect(10, 0, 60, 15, 'F')
        pdf.set_xy(10, 20)
        pdf.set_font("helvetica", "B", 26)
        pdf.cell(60, 15, name.upper(), ln=1)
        pdf.rect(10, 38, 60, 259, 'F')
        pdf.set_xy(15, 45); pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 12); pdf.cell(50, 8, "Personal details", ln=1)
        pdf.line(15, 53, 65, 53)
        pdf.set_font("helvetica", "", 9)
        pdf.set_xy(15, 60); pdf.multi_cell(45, 5, f"Email:\n{details.get('email')}\n\nPhone:\n{details.get('phone')}\n\nAddress:\n{details.get('address')}")
        pdf.set_xy(80, 40); pdf.set_text_color(0, 0, 0); pdf.multi_cell(115, 5, content)
    else:
        # Style 2: Minimalist
        pdf.set_fill_color(242, 242, 242); pdf.rect(0, 0, 75, 297, 'F')
        pdf.set_fill_color(r, g, b); pdf.rect(0, 0, 75, 25, 'F')
        pdf.ellipse(-10, 10, 95, 30, 'F')
        pdf.set_xy(5, 12); pdf.set_font("helvetica", "B", 18); pdf.set_text_color(255, 255, 255); pdf.cell(65, 10, name, align="C")
        pdf.set_xy(10, 50); pdf.set_text_color(r, g, b); pdf.set_font("helvetica", "B", 14); pdf.cell(55, 8, "Contact Info", ln=1)
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10); pdf.set_xy(10, 60)
        pdf.multi_cell(55, 6, f"{details.get('email')}\n{details.get('phone')}\n{details.get('address')}")
        pdf.set_xy(85, 15); pdf.multi_cell(110, 5, content)

    return bytes(pdf.output())

# --- UI ---
st.title("📄 AI Cover Letter Designer")

with st.form("input_form"):
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Name", "Jane Fitz")
        email = st.text_input("Email", "jane@example.com")
        phone = st.text_input("Phone", "(222) 345-6789")
        address = st.text_input("Address", "Scranton, PA")
    with c2:
        pos = st.text_input("Position")
        comp = st.text_input("Company")
        skls = st.text_area("Skills")
    
    t_style = st.selectbox("Style", ["Template 1 - Sidebar Bold", "Template 2 - Sidebar Minimal"])
    t_color = st.selectbox("Color", ["Teal", "Forest Green", "Navy Blue", "Burgundy", "Charcoal"])
    
    if st.form_submit_button("Generate"):
        with st.spinner("Writing..."):
            prompt = f"Professional cover letter for {name} for {pos} at {comp}. Skills: {skls}."
            res = client.chat.completions.create(model="llama3-8b-8192", messages=[{"role": "user", "content": prompt}])
            st.session_state.full_letter = f"Hiring Manager\n{comp}\n\n{datetime.now().strftime('%B %d, %Y')}\n\n{res.choices[0].message.content}"
            st.session_state.data = {"name":name, "email":email, "phone":phone, "address":address, "tmpl":t_style, "clr":t_color}

if st.session_state.get("full_letter"):
    st.divider()
    edited = st.text_area("Edit text:", value=st.session_state.full_letter, height=300)
    pdf_out = generate_pdf(st.session_state.data["tmpl"], st.session_state.data["clr"], st.session_state.data, edited)
    st.download_button("Download PDF", data=pdf_out, file_name="CoverLetter.pdf", mime="application/pdf")
