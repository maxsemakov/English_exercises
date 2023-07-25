from flask import Flask, render_template, request, jsonify
import json
import os
import pandas as pd
from text_convertor import FB2Reader, get_text_from_docx_file

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
        text_evaluate = ""
        descriptions = {}
        types = {}
        answers = {}
        for paragraph_value in result_df['paragraph'].unique():
            paragraph_df = result_df[result_df['paragraph'] == paragraph_value]
            paragraph_text = ""
            paragraph_text_evaluate = ""

            for i, row in paragraph_df.iterrows():
                sentence = row['sentence_exercise']
                sentence_evaluate = sentence
                if pd.isna(sentence):
                    continue
                options = row['options']
                
                if row['options'] is None:
                    sentence = sentence.replace("___", f"<input type='text' name='user_answer_{i}'>")
                    sentence_evaluate = sentence_evaluate.replace("___", f"<span class='user-answer' data-index='{i}'></span>")
                else:
                    options_list = options
                    select_options = "".join([f"<option value='{opt.strip()}'>{opt.strip()}</option>" for opt in options_list])
                    sentence = sentence.replace("___", f"<select name='user_answer_{i}'><option value='' selected disabled hidden></option>{select_options}</select>")
                    sentence_evaluate = sentence_evaluate.replace("___", f"<span class='user-answer' data-index='{i}'></span>")
                paragraph_text += sentence + " "
                paragraph_text_evaluate += sentence_evaluate + " "
                descriptions[i] = row['description']
                types[i] = row['type']
                answers[i] = row['answer']
            text += f"<p>{paragraph_text}</p>"
            text_evaluate += f"<p>{paragraph_text_evaluate}</p>"

        data = {
            'descriptions': descriptions,
            'types': types,
            'answers': answers
        }
        answers_json = json.dumps(answers)

        return render_template('exercises.html', text=text, text_evaluate=text_evaluate, data=data, answers_json = answers_json)
    else:
        # обработка случая, когда данные не переданы
        return render_template('error.html')
    
@app.route('/exercise_evaluation', methods=['POST'])
def exercise_evaluation():
    # получение данных из формы
    user_answers = request.form.to_dict()
    text_evaluate = request.form.get('text_evaluate')
    answers_json = request.form.get('answers')
    answers = json.loads(answers_json)
    # сравнение ответов пользователя с правильными ответами
    # и замена текста в text_evaluate
    for index in range(len(answers)):
        value = user_answers.get(f'user_answer_{index}', '')
        if value == answers[str(index)]:
            text_evaluate = text_evaluate.replace(f"<span class='user-answer' data-index='{index}'></span>", f"<span class='user-answer text-success' data-index='{index}'>{value}</span>")
        else:
            text_evaluate = text_evaluate.replace(f"<span class='user-answer' data-index='{index}'></span>", f"<span class='user-answer text-danger' data-index='{index}'>{value}</span>")
    # рендеринг шаблона с результатами
    return render_template('exercise_evaluation.html', text=text_evaluate)

if __name__ == "__main__":
    app.run(debug=True)