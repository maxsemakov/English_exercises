#!/usr/bin/env python
# coding: utf-8


import subprocess
import sys
    
try:
    import spacy
    print('Библиотека spacy уже установлена')
except ImportError:
    print('Библиотека spacy не установлена. Установка...')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'spacy'])
    import spacy

import os
import re
import pandas as pd
import csv
import nltk

import random


from nltk.corpus import brown

from nltk.corpus import brown

try:
    # Попытка загрузить корпус brown
    brown.words()
except LookupError:
    # Если корпус не найден, загрузить его
    nltk.download('brown')

try:
    nlp = spacy.load('en_core_web_sm')
    print('Модель en_core_web_sm установлена')
except OSError:
    print('Модель en_core_web_sm не установлена. Загрузка...')
    subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    print('Модель en_core_web_sm загружена')


def split_text(text, output_dir='split_text', n=20):
    # Открыть текстовый файл и прочитать его содержимое

    # Разбить текст на абзацы по переносам строк
    paragraphs = text.split('\n')

    # Разбить абзацы на предложения по символам .!? или переносу строки, сохраняя символ " в тексте
    sentences = []
    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            sentences.append(('', i + 1))
        else:
            paragraph_sentences = re.split(r'(?<=[.!?])\s+|(?<=\.)"(?!\s)|(?<=\.\.\.)"|(?<=\?)"|(?<=!)"', paragraph)
            for sentence in paragraph_sentences:
                sentences.append((sentence, i + 1))

    # Разбить предложения на блоки по n непустых строк
    blocks = []
    block = []
    non_empty_count = 0
    for sentence, paragraph in sentences:
        block.append((sentence, paragraph))
        if sentence.strip():
            non_empty_count += 1
        if non_empty_count == n:
            blocks.append(block)
            block = []
            non_empty_count = 0
    if block:
        blocks.append(block)

    # Удалить все существующие файлы в директории вывода
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.endswith('.csv'):
                os.remove(os.path.join(output_dir, file))
    else:
        os.makedirs(output_dir)

    # Сохранить каждый блок в отдельный csv файл
    for i, block in enumerate(blocks):
        with open(os.path.join(output_dir, f'block_{i}.csv'), 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['raw', 'paragraph'])
            for sentence, paragraph in block:
                writer.writerow([sentence, paragraph])


class ExercisesGeneration:
    def __init__(self, df,  exercise_types=['determiners'], topics=['grammar']):
        self.df = df
        self.exercise_types = exercise_types
        self.topics = topics

    def generate(self, path='exercise_ready/'):
        result = []
        ex = exercises(self.df)
        for index, row in self.df.iterrows():
            sentence = str(row[0])
            parsed_sentence = self.sentence_to_dict(sentence)
            exercise = self.select_exercise(parsed_sentence, index, ex)
            result.append({
                "raw": sentence,
                "paragraph": int(row[1]),
                "type": exercise["type"],
                "sentence_exercise": exercise["sentence_exercise"],
                "object": exercise["object"],
                "options": exercise["options"],
                "answer": exercise["answer"],
                "description": exercise["description"]
            })

        result_df = pd.DataFrame(result)
""""""
        # Сохранение результата в файл CSV

        if not os.path.exists(path):
            os.makedirs(path)

        # Удаление существующих файлов в директории
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

        result_df.to_csv(f'{path}result.csv', index=False)

        return result_df

    def sentence_to_dict(self, sentence):
        # Загрузка модели spaCy для английского языка
        nlp = spacy.load('en_core_web_sm')
        doc = nlp(sentence)

        result = []
        for token in doc:
            word_dict = {}
            word_dict['word'] = token.text
            word_dict['part_of_speech'] = token.pos_
            word_dict['sentence_member'] = token.dep_
            word_dict['lemma'] = token.lemma_  # add lemma attribute
            word_dict['index'] = token.i  # add index attribute

            result.append(word_dict)

        return result

    def select_exercise(self, parsed_sentence, row_index, ex):
        # Запрашиваем какие функции есть в наличии у класса exercise
        function_info = ex.get_function_info()
        # Создаем список из имен функций
        function_names = list(function_info.keys())

        # Перемешиваем список, чтобы выбирать случайное упражнение
        random.shuffle(function_names)
        # Проходим по списку функций и проверяем условия для каждой
        for function_name in function_names:
            # Получаем условия для функции из словаря function_info
            conditions = function_info[function_name]['conditions']

            # Проверяем, выполняются ли условия для предложения

            if self.check_conditions(parsed_sentence, conditions):
                # Если да, то вызываем функцию и возвращаем результат
                getattr(ex, function_name)(row_index, parsed_sentence)

                return {
                    "type": ex.df.loc[row_index, 'type'],
                    "sentence_exercise": ex.df.loc[row_index,
                                                   'sentence_exercise'],
                    "object": ex.df.loc[row_index, "object"],
                    "options": ex.df.loc[row_index, "options"],
                    "answer": ex.df.loc[row_index, "answer"],
                    "description": ex.df.loc[row_index, "description"]
                }

        # Если ни одна функция не подходит, то возвращаем заглушку
        return {
            "type": None,
            "sentence_exercise": None,
            "object": None,
            "options": None,
            "answer": None,
            "description": None
        }

    def check_conditions(self, parsed_sentence, conditions):
        # Эта функция проверяет, выполняются ли условия для предложения
        # Условия задаются в виде списка кортежей вида (атрибут, значение)
        # Например: [('part_of_speech', 'DET'), ('length', 4)]
        # Это означает, что в предложении должен быть определитель и длина предложения должна быть больше 4
        for condition in conditions:
            attribute, value = condition
            # Проверяем атрибуты слов в предложении
            if attribute in ['word', 'part_of_speech', 'sentence_member', 'lemma']:
                # Если атрибут не соответствует значению ни для одного слова, то условие не выполняется

                if not any(word[attribute] == value for word in parsed_sentence):
                    return False
            # Проверяем длину предложения
            elif attribute == 'length':
                # Если длина предложения меньше или равна значению, то условие не выполняется
                if len(parsed_sentence) <= value:
                    return False
            # Проверяем другие атрибуты по необходимости
            else:
                # Если атрибут не поддерживается или неизвестен, то условие не выполняется
                return False
        # Если все условия выполняются, то возвращаем True
        return True






class exercises:
    def __init__(self, df):
        self.df = df
        self.df = self.df.assign(options=None, type=None, sentence_exercise=None, object=None, answer=None, description=None)
            
        self.function_description = { 
            "missing_word" :  {"arguments": None, "returns": None, "description": "Выбери пропущенное слово", 
            "conditions": [("part_of_speech", "NOUN"),
            ("length", 5),
            #("word", ".islower()")
                          ]},
            "determiners" :  {"arguments": None, "returns": None, "description": """Выбери правильный определитель""", 
            "conditions": [("part_of_speech", "DET"),
            ("length", 4)]}}
            




    def set_exercise(self, row_index, exercise_type, object, options, answer, description):
    # Эта функция устанавливает параметры для упражнения в датафрейме
    # Добавляем переменные для аргументов, возвращаемого значения и условий функции после того, как они определены
        sentence_dict = self.sentence_dict

        self.df.at[row_index, "type"] = exercise_type

    # Генерируем sentence_exercise, ища объект в предложении по его слову или выражению
        object_index = None
    # Если объект состоит из одного слова, то ищем его по слову
        if isinstance(object, str):
            for word in sentence_dict:
                if word['word'] == object:
                    object_index = word['index']
                    break
    # Если объект состоит из нескольких слов, то ищем его по выражению
        elif isinstance(object, list):
            for i in range(len(sentence_dict) - len(object) + 1):
                if [word['word'] for word in sentence_dict[i:i + len(object)]] == object:
                    object_index = (i, i + len(object) - 1)
                    break

    # Если объект не найден, то возвращаем None
        if object_index is None:
            return None

    # Создаем список слов предложения
        sentence_words = []
        sentence_words = [word['word'] for word in sentence_dict]
    # Заменяем слово или слова объекта на '___'
        if isinstance(object_index, int):
            sentence_words[object_index] = '___'
        elif isinstance(object_index, tuple):
            for i in range(object_index[0], object_index[1] + 1):
                sentence_words[i] = '___'

    # Соединяем слова предложения в строку
        sentence_exercise = ' '.join(sentence_words)

        self.df.at[row_index, "sentence_exercise"] = sentence_exercise
        self.df.at[row_index, "object"] = object
        self.df.at[row_index, "options"] = options
        self.df.at[row_index, "answer"] = answer
        self.df.at[row_index, "description"] = description

    def determiners(self, row_index, sentence_dict):
        """Выбери правильный определитель"""
        self.sentence_dict = sentence_dict
        det_list = ['a', 'an', 'the', 'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our', 'their']
        # Выбираем определитель только тот, который есть в предложении
        det_choice = None
        for word in sentence_dict:
            if word['part_of_speech'] == 'DET' and word['word'] in det_list:
                det_choice = word['word']
                break
        # Если определитель не найден, то возвращаем None
        if not det_choice:
            return None
        
        options = []
        if det_choice in ['a', 'an', 'the']:
            options = [det for det in ['a', 'an', 'the'] if det != det_choice]
        elif det_choice in ['this', 'that', 'these', 'those']:
            options = random.sample([det for det in ['this', 'that', 'these', 'those'] if det != det_choice], 2)
        elif det_choice in ['my', 'your', 'his', 'her', 'its', 'our', 'their']:
            options = random.sample([det for det  in ['my', 'your', 'his', 'her', 'its', 'our', 'their'] if det != det_choice], 2)
        
        options.append(det_choice)
        random.shuffle(options)
        
        answer = det_choice
        description = self.determiners.__doc__
        # Используем функцию set_exercise для установки параметров в датафрейме, передавая все необходимые аргументы
        self.set_exercise(row_index, "determiners", det_choice, options, answer, description)

    def missing_word(self, row_index, sentence_dict):
        """Выбери пропущенное слово"""

        self.sentence_dict = sentence_dict
        noun_list = [word for word in sentence_dict if word['part_of_speech'] == 'NOUN' and word['word'] != word['word'].capitalize()]
        if noun_list:
            noun_choice = random.choice(noun_list)
            noun_word = noun_choice['word']
            options = None
            

            answer = noun_word
            description = self.missing_word.__doc__
            # Используем функцию set_exercise для установки параметров в датафрейме, передавая все необходимые аргументы
            self.set_exercise(row_index, "missing_word", noun_word, options, answer, description)

    def get_function_info(self):
        
        result = self.function_description
            
            
            
        return result   


# In[16]:

