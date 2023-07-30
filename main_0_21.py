from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
from text_convertor import FB2Reader, get_text_from_docx_file
import docx
from English_exercises_0_18 import split_text, ExercisesGeneration

app = Flask(__name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'fb2', 'txt', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_file():
    if os.path.exists('split_text/block_0.csv'):
        df = pd.read_csv('split_text/block_0.csv')
        ex_gen = ExercisesGeneration(df)
        result_df = ex_gen.generate()
        return result_df, 'block_0.csv'
    else:
        return None, None

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
        
        # вызов функции process_file
        result_df, csv_file = process_file()
        if result_df is not None:
            # преобразование result_df в JSON-формат
            result_json = result_df.to_json()
            return jsonify({'success': True, 'result': result_json, 'csv_file': csv_file})
        else:
            return jsonify({'success': False, 'error': 'Ошибка обработки файла'})
    else:
        return jsonify({'success': False, 'error': 'Неверный тип файла'})

@app.route('/exercises', methods=['GET', 'POST'])

def render_exercises():
    # получение данных из параметров запроса
    result_json = request.args.get('result')
    csv_file = request.args.get('csv_file')
    if result_json is not None and csv_file is not None:
        # преобразование JSON-строки в DataFrame
        result_df = pd.read_json(result_json)
        
        # Создание текста для каждой строки в DataFrame
        text = ""
        descriptions = {}
        types = {}
        answers = {}
        for paragraph_value in result_df['paragraph'].unique():
            paragraph_df = result_df[result_df['paragraph'] == paragraph_value]
            paragraph_text = ""

            for i, row in paragraph_df.iterrows():
                sentence = row['sentence_exercise']
                if pd.isna(sentence):
                    continue
                options = row['options']
                
                if row['options'] is None:
                    sentence = sentence.replace("___", f"<input type='text' name='user_answer_{i}'>")
                else:
                    options_list = options
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
    else:
        # обработка случая, когда данные не переданы
        return render_template('error.html')

if __name__ == "__main__":
    app.run(debug=True)