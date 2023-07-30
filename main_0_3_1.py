from flask import Flask, render_template, request, jsonify, request, render_template, session
from flask_caching import Cache
import os
import pandas as pd
from text_convertor import FB2Reader, get_text_from_docx_file
from English_exercises_0_2 import split_text, ExercisesGeneration, save_result_csv

app = Flask(__name__)
app.secret_key = '42'
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

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
    filename = request.form['filename']
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
        # сохранение данных в сессии
        save_result_csv(result_df)
        
        session['csv_file'] = csv_file
        

        return jsonify(success=True, csv_file=csv_file, filename=filename)
    else:
        return jsonify(success=False, error='Ошибка обработки файла')


@app.route('/exercises', methods=['GET', 'POST'])

def render_exercises():
    # получение данных из параметров запроса
    
    result_df = pd.read_csv('exercise_ready/result.csv')
    csv_file = session.get('csv_file')
    print(csv_file, 'in exercise')
    if result_df is not None and csv_file is not None:
        # преобразование JSON-строки в DataFrame
        
        print(result_df)
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
                #print(row)
                sentence = row['sentence_exercise']
                sentence_evaluate = sentence
                if pd.isna(sentence):
                    continue

                
                if row['type'] == 'scrambled_words':
                # Обработка упражнения scrambled_words
                    print(f'Drag&drop exercise #{i}')
                    options_list = eval(row.loc['options'])

                    sentence_parts = row['sentence_exercise'].split('___')
                    sentence = f"<ul class='sortable' name='user_answer_{i}' data-index='{i}'>"
                    for n, part in enumerate(sentence_parts):
                        sentence += part
                        if n < len(options_list):
                            word = options_list[n]
                            sentence += f"<li class='ui-state-default' data-word='{word}'>{word}</li>"
                    sentence += "</ul>"
                    sentence_evaluate = sentence
                    
                elif pd.isna(row['options']):
                    sentence = sentence.replace("___", f"<input type='text' name='user_answer_{i}'>")
                    sentence_evaluate = sentence_evaluate.replace("___", f"<span class='user-answer' data-index='{i}'></span>")
                else:
                    options_list = eval(row.loc['options'])
                    select_options = "".join([f"<option value='{opt.strip()}'>{opt.strip()}</option>" for opt in options_list])
                    sentence = sentence.replace("___", f"<select name='user_answer_{i}'><option value='' selected disabled hidden></option>{select_options}</select>")
                    sentence_evaluate = sentence_evaluate.replace("___", f"<span class='user-answer' data-index='{i}'></span>")
                paragraph_text += sentence + " "
                paragraph_text_evaluate += sentence_evaluate + " "

                descriptions[i] = row['description']
                #print(descriptions[i])
                types[i] = row['type']
                
                if row['type'] == 'scrambled_words':
                    answers[i] = eval(row['answer'])
                    print(f'для индекса {i} ответ:')
                    print(answers[i])
                else:
                    answers[i] = row['answer']

            text += f"<p>{paragraph_text}</p>"
            text_evaluate += f"<p>{paragraph_text_evaluate}</p>"

        data = {
            'descriptions': descriptions,
            'types': types,
            'answers': answers
        }

        
       
        # сохранение данных в кэше
        cache.set('data', data)
        cache.set('text_evaluate', text_evaluate)

        return render_template('exercises.html', text=text, data=data)
    else:
        # обработка случая, когда данные не переданы
        return render_template('error.html')
    
@app.route('/exercise_evaluation', methods=['POST'])
def exercise_evaluation():
    # получение данных из формы и сессии
    user_answers = request.form.to_dict()
    print(f'ответы пользователя{user_answers}')
    text_evaluate = cache.get('text_evaluate')
    data = cache.get('data')
    answers = data['answers']
    print(f'ответы правильные{answers}')
    descriptions = data['descriptions']

    #if cache.get('data') is not None and cache.get('text_evaluate') is not None:
    #    cache.delete('data')
    #    cache.delete('text_evaluate')

    # подсчет количества правильных ответов
    correct_answers = 0
    for key in answers:
        user_answer_key = f'user_answer_{key}'
        if user_answer_key in user_answers:
            value = user_answers[user_answer_key]
            if answers[key] == value:
                correct_answers += 1

    # создание списка ошибок
    errors = []
    for key in answers:
        user_answer_key = f'user_answer_{key}'
        if user_answer_key in user_answers:
            value = user_answers[user_answer_key]
            if answers[key] != value:
                error = {
                    'index': key,
                    'description': descriptions[key],
                    'user_answer': value,
                    'correct_answer': answers[key]
                }
                errors.append(error)

    # проверка наличия всех ключей в словаре answers
    for key in answers:
        user_answer_key = f'user_answer_{key}'
        if user_answer_key not in user_answers:
            # ключ отсутствует, обработка ошибки
            print(f"Error: key '{user_answer_key}' not found in user_answers")
        else:
            # ключ найден, проверка соответствия значений
            value = user_answers[user_answer_key]
            if answers[key] == value:
                text_evaluate = text_evaluate.replace(f"<span class='user-answer' data-index='{key}'></span>", f"<span class='user-answer bg-success text-white' data-index='{key}'> {value}</span>")
            else:
                if value == '':
                    value = '__'
                text_evaluate = text_evaluate.replace(f"<span class='user-answer' data-index='{key}'></span>", f"<span class='user-answer bg-danger text-white' data-index='{key}'> {value}</span>")

    return render_template('exercise_evaluation.html', text=text_evaluate, correct_answers=correct_answers, total_questions=len(answers), errors=errors)


if __name__ == "__main__":
    app.run(debug=True)