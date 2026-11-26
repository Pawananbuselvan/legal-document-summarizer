from flask import Flask, request, render_template, jsonify
import PyPDF2
import sqlite3
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import google.generativeai as genai
import os

# Download local NLP data for the offline engine
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

app = Flask(__name__)

# --- AI API SETUP ---
# If you want to use the AI option, get a free API key from Google AI Studio and paste it here.
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
genai.configure(api_key=GEMINI_API_KEY)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('summaries.db')
    cursor = conn.cursor()
    # Added an 'engine' column to track if it was summarized offline or by AI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            summary TEXT,
            engine TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- ENGINE 1: OFFLINE NLP (EXTRACTIVE) ---
def summarize_offline(text, length_mode):
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(text)
    
    # 1. Count how many times important words appear
    freq_table = dict()
    for word in words:
        word = word.lower()
        if word not in stop_words and word.isalnum():
            freq_table[word] = freq_table.get(word, 0) + 1

    # 2. Score sentences based on the important words inside them
    sentences = sent_tokenize(text)
    sentence_value = dict()
    for sentence in sentences:
        for word, freq in freq_table.items():
            if word in sentence.lower():
                sentence_value[sentence] = sentence_value.get(sentence, 0) + freq

    # 3. Determine how many sentences to keep based on user dropdown choice
    if length_mode == "one_page":
        target_length = min(len(sentences), 20) # Keep top 20 sentences for a 1-page feel
    else:
        target_length = int(len(sentences) * 0.20) # Auto mode: Keep top 20%
        if target_length == 0:
            target_length = min(len(sentences), 2)
            
    # 4. Sort and extract the best sentences
    sorted_sentences = sorted(sentence_value, key=sentence_value.get, reverse=True)
    return " ".join(sorted_sentences[:target_length])

# --- ENGINE 2: AI API (ABSTRACTIVE) ---
def summarize_ai(text, length_mode):
    # Safety check if you haven't pasted your API key yet
    if GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        return "API ERROR: Please paste your real Gemini API key in app.py to use the AI Engine."
    
    # Build a specific prompt for the AI based on the user's dropdown choice
    if length_mode == "one_page":
        prompt = "Read this document and write a highly detailed 1-page summary covering all major clauses and dates:\n\n"
    else:
        prompt = "Read this document and write a short, general summary of the main points:\n\n"
        
    prompt += text[:15000] # Limit text length so we don't overload the free API limit

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Generation Failed: {str(e)}"

# --- FLASK ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    # 1. Get the file and the dropdown choices from the HTML frontend
    file = request.files.get('file')
    engine_choice = request.form.get('engine', 'offline')
    length_choice = request.form.get('length', 'auto')

    if not file or file.filename == '':
        return jsonify({"error": "No file uploaded"})

    # 2. Extract text from the PDF safely
    pdf_reader = PyPDF2.PdfReader(file)
    extracted_text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_text += page_text

    if not extracted_text.strip():
        return jsonify({"error": "Could not extract text. The PDF might be scanned or image-based."})

    # 3. Route the text to the correct engine
    if engine_choice == 'ai':
        final_summary = summarize_ai(extracted_text, length_choice)
    else:
        final_summary = summarize_offline(extracted_text, length_choice)

    # 4. Log it in the SQLite database
    conn = sqlite3.connect('summaries.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO documents (filename, summary, engine) VALUES (?, ?, ?)", 
                   (file.filename, final_summary, engine_choice))
    conn.commit()
    conn.close()

    # 5. Send it back to the HTML frontend
    return jsonify({"summary": final_summary})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)