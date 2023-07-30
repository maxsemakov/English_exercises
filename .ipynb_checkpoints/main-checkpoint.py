from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Загрузка данных из файла CSV в DataFrame
    df = pd.read_csv('exercise_ready/result.csv')

    # Создание текста для каждой строки в DataFrame
    text = ""
    user_answers = {}
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
                user_answers[i] = None
            else:
                options_list = eval(row.loc['options'])
                select_options = "".join([f"<option value='{opt.strip()}'>{opt.strip()}</option>" for opt in options_list])
                sentence = sentence.replace("___", f"<select name='user_answer_{i}'>{select_options}</select>")
                user_answers[i] = None
            paragraph_text += sentence + " "
        text += f"<p>{paragraph_text}</p>"

    if request.method == 'POST':
        for i in user_answers.keys():
            answer = request.form.get(f'user_answer_{i}')
            if answer:
                user_answers[i] = answer

    return render_template('index.html', text=text)

if __name__ == "__main__":
    app.run(debug=True)