from flask import Flask, render_template, request
import pandas as pd
import pandas as pd
from text_convertor import FB2Reader, get_text_from_docx_file
import docx
from English_exercises_0_18 import split_text, 



app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file and allowed_file(file.filename):
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        if file_ext == 'fb2':
            file_content = file.read().decode('utf-8')
            reader = FB2Reader(file_content)
            text = reader.get_text()
            
        elif file_ext == 'txt':
            text = file.read().decode('utf-8')
        elif file_ext == 'docx':
            text = get_text_from_docx_file(file)
        else:
            text = 'Invalid file type'
        split_text(text)
        return 'File processed successfully'
    else:
        return 'Invalid file type'

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'fb2', 'txt', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_text_from_docx(file_path):
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

@app.route('/exercises', methods=['GET', 'POST'])
def render_exercises():
    # Загрузка данных из файла CSV в DataFrame
    df = pd.read_csv('exercise_ready/result.csv')

    # Создание текста для каждой строки в DataFrame
    text = ""
    descriptions = {}
    types = {}
    answers = {}
    for paragraph_value in df['paragraph'].unique():
        paragraph_df = df[df['paragraph'] == paragraph_value]
        paragraph_text = ""
        for i, row in paragraph_df.iterrows():
            sentence = row['sentence_exercise']
            if pd.isna(sentence):
                continue
            options = row['options']
            if pd.isna(row['options']):
                sentence = sentence.replace("___", f"<input type='text' name='user_answer_{i}'>")
            else:
                options_list = eval(row.loc['options'])
                select_options = "".join([f"<option value='{opt.strip()}'>{opt.strip()}</option>" for opt in options_list])
                sentence = sentence.replace("___", f"<select name='user_answer_{i}'><option value='' selected disabled hidden></option>{select_options}</select>")
            paragraph_text += sentence + " "
            descriptions[i] = row['description']
            types[i] = row['type']
            answers[i] = row['answer']
        text += f"<p>{paragraph_text}</p>"

    data = {
        'descriptions': descriptions,
        'types': types,
        'answers': answers
    }

    return render_template('exercises.html', text=text, data=data)

if __name__ == "__main__":
    app.run(debug=True)
