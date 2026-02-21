import streamlit as st
import os
import re
from groq import Groq
from fpdf import FPDF
from datetime import datetime

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="AI Cover Letter Pro", page_icon="📄", layout="wide")

# --- 2. API SETUP ---
try:
    # Ensure your GROQ_API_KEY is added to Streamlit Secrets
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("🔑 GROQ_API_KEY not found in Streamlit Secrets.")
    st.stop()

# --- 3. SESSION STATE INITIALIZATION ---
if "letter_body" not in st.session_state:
    st.session_state["letter_body"] = ""
if "form_data" not in st.session_state:
    st.session_state["form_data"] = {}
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
if "first_gen_time" not in st.session_state:
    st.session_state.first_gen_time = datetime.now()

# --- 4. HELPERS & VALIDATION ---
def is_text_only(text):
    return bool(re.match(r"^[a-zA-Z\s]*$", text))

def validate_phone(phone):
    """Validates: Starts with '+', Country Code 1-3, Subscriber Max 12."""
    if not phone.startswith('+'):
        return False, "Phone must start with '+'"
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 2 or len(digits) > 15:
        return False, "Phone must have 1-3 digit country code and max 12 digit subscriber number."
    return True, ""

def clean_for_pdf(text):
    """Fixes smart quotes/dashes that crash FPDF."""
    replacements = {'\u2018':"'", '\u2019':"'", '\u201c':'"', '\u201d':'"', '\u2013':"-", '\u2014':"-", '\u2026':"..."}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

# --- 5. PDF GENERATION ENGINE ---
def generate_pdf(template, color_name, details, content):
    colors = {"Teal": (52, 165, 173), "Navy Blue": (0, 51, 102), "Charcoal": (54, 69, 79), "Burgundy": (128, 0, 32)}
    r, g, b = colors.get(color_name, (52, 165, 173))
    
    pdf = FPDF(unit="mm", format="A4")
    pdf.add_page()
    content = clean_for_pdf(content)
    today = datetime.now().strftime("%B %d, %Y") # Fixes missing date [cite: 5, 8, 40, 42]

    if "Traditional" in template:
        # Header: Name and dynamic contact info [cite: 1-2, 30-33]
        pdf.set_font("times", "B", 24)
        pdf.cell(0, 15, details['name'], ln=True, align="C")
        pdf.set_font("times", "", 10)
        
        contact_parts = [details['address'], details['phone'], details['email']]
        if details.get('linkedin'):
            contact_parts.append(f"LinkedIn: {details['linkedin']}")
        pdf.cell(0, 5, " | ".join(contact_parts), ln=True, align="C")
        
        pdf.set_draw_color(r, g, b); pdf.line(20, 35, 190, 35)
        pdf.ln(10)
        
        # Date & Recipient Block [cite: 3-4, 9-11, 45-47]
        pdf.set_font("times", "", 11)
        pdf.cell(0, 6, today, ln=True)
        pdf.ln(5)
        pdf.set_font("times", "B", 11)
        pdf.cell(0, 6, "Hiring Manager", ln=True)
        pdf.set_font("times", "", 11)
        pdf.cell(0, 6, details['company'], ln=True)
        pdf.cell(0, 6, "Company Headquarters", ln=True)
        
        pdf.ln(10)
        pdf.multi_cell(0, 6, content)
        
        # Attachment line [cite: 27]
        pdf.ln(10); pdf.set_font("times", "B", 11)
        pdf.cell(0, 6, "Attachment: Resume", ln=True)

    else: # Template 2 - Sidebar Minimal [cite: 34-38, 52-53, 60]
        pdf.set_fill_color(242, 242, 242); pdf.rect(0, 0, 75, 297, 'F')
        pdf.set_fill_color(r, g, b); pdf.rect(0, 0, 75, 25, 'F')
        pdf.ellipse(-10, 10, 95, 30, 'F')
        pdf.set_xy(5, 12); pdf.set_font("helvetica", "B", 18); pdf.set_text_color(255, 255, 255)
        pdf.cell(65, 10, details['name'], align="C")
        pdf.set_xy(10, 50); pdf.set_text_color(r, g, b); pdf.set_font("helvetica", "B", 12)
        pdf.cell(55, 8, "CONTACT DETAILS", ln=1)
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 9); pdf.set_xy(10, 60)
        
        c_info = f"Email: {details['email']}\n\nPhone: {details['phone']}\n\nAddress: {details['address']}"
        if details.get('linkedin'):
            c_info += f"\n\nLinkedIn:\n{details['linkedin']}"
        pdf.multi_cell(55, 5, c_info)
        
        pdf.set_xy(80, 20); pdf.set_font("helvetica", "", 10)
        pdf.multi_cell(115, 5, f"{today}\n\nTo: Hiring Manager\n{details['company']}\n\n{content}\n\nAttachment: Resume")

    return bytes(pdf.output())

# --- 6. UI FORM ---
st.title("📄 Professional AI Cover Letter Designer")

with st.form("cv_form"):
    c1, c2 = st.columns(2)
    with c1:
        u_name = st.text_input("Full Name")
        u_email = st.text_input("Email Address")
        u_phone = st.text_input("Phone Number", placeholder="+923324979753")
        u_addr = st.text_input("City, Country", placeholder="Karachi, Pakistan")
        u_link = st.text_input("LinkedIn URL", placeholder="https://www.linkedin.com/in/yourprofile")
    with c2:
        u_pos = st.text_input("Target Position")
        u_comp = st.text_input("Company Name")
        u_skls = st.text_area("Skills & Experience")
    
    t_style = st.selectbox("Template Style", ["Traditional - Classic Times", "Template 2 - Sidebar Minimal"])
    t_color = st.selectbox("Color Theme", ["Teal", "Navy Blue", "Charcoal", "Burgundy"])
    submit = st.form_submit_button("Generate Professional Letter", type="primary")

# --- 7. LOGIC & RATE LIMITING ---
if submit:
    # 1-Hour Time Window Check
    time_passed = (datetime.now() - st.session_state.first_gen_time).total_seconds()
    if time_passed > 3600:
        st.session_state.gen_count = 0
        st.session_state.first_gen_time = datetime.now()

    # Validations
    p_valid, p_err = validate_phone(u_phone)
    error = False
    if st.session_state.gen_count >= 5:
        st.error(f"🚫 Hourly Limit Reached. Wait {int((3600-time_passed)/60)} minutes.")
        error = True
    elif not all([u_name, u_email, u_phone, u_addr, u_pos, u_comp]):
        st.error("All main fields are required.")
        error = True
    elif len(u_addr.split()) < 2:
        st.error("Please provide a full address (City, Country).")
        error = True
    elif not p_valid:
        st.error(p_err)
        error = True
    elif u_link and not u_link.startswith("https://www.linkedin.com/in/"):
        st.error("LinkedIn must start with https://www.linkedin.com/in/")
        error = True

    if not error:
        with st.spinner("AI is crafting your letter..."):
            try:
                # Prompt forces contact info in closing [cite: 30-32, 60]
                prompt = (
                    f"Write a professional cover letter for {u_name} for {u_pos} at {u_comp}. Skills: {u_skls}. "
                    "STRICT RULES: No header/date/brackets. Start with 'Dear Hiring Manager'. "
                    f"In the closing paragraph, strictly include: 'I can be reached at {u_phone} or {u_email} to discuss further.' "
                    f"End with 'Sincerely, {u_name}'."
                )
                response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                st.session_state.letter_body = response.choices[0].message.content
                st.session_state.gen_count += 1
                st.session_state.form_data = {"name":u_name, "email":u_email, "phone":u_phone, "address":u_addr, "company":u_comp, "linkedin":u_link, "tmpl":t_style, "clr":t_color}
            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- 8. PREVIEW & DOWNLOAD ---
if st.session_state.letter_body:
    st.divider()
    final_text = st.text_area("Edit Content:", value=st.session_state.letter_body, height=300)
    pdf_bytes = generate_pdf(st.session_state.form_data['tmpl'], st.session_state.form_data['clr'], st.session_state.form_data, final_text)
    st.download_button("Download Professional PDF", data=pdf_bytes, file_name=f"{u_name.replace(' ','_')}_CoverLetter.pdf", mime="application/pdf")
