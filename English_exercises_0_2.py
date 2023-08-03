#!/usr/bin/env python
# coding: utf-8

import subprocess
import sys


try:
    import nltk
    print('Библиотека nltk уже установлена')
except ImportError:
    print('Библиотека nltk не установлена. Установка...')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'nltk'])
    import nltk

    
try:
    import spacy
    print('Библиотека spacy уже установлена')
except ImportError:
    print('Библиотека spacy не установлена. Установка...')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'spacy'])
    import spacy
    
try:
    nlp = spacy.load('en_core_web_sm')
    print('Модель en_core_web_sm установлена')
except OSError:
    print('Model en_core_web_sm is not installed. Downloading...')
    subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    print('Model en_core_web_sm has been downloaded')
    try:
        nlp = spacy.load('en_core_web_sm')
        print('Модель en_core_web_sm установлена')
    except OSError:
        print('Model en_core_web_sm is not installed. ')

import os
import re
import pandas as pd
import csv


import random


from nltk.corpus import wordnet

try:
       
    wordnet.words()
except LookupError:
    # Если корпус не найден, загрузить его

    nltk.download('wordnet')




def split_text(text, output_dir='split_text', n=16):


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
    def __init__(self, df, exercise_types=None, topics=['grammar']):
        self.df = df
        self.exercise_types = exercise_types
        self.topics = topics

    def generate(self):
        result = []
        ex = exercises(self.df)
        for index, row in self.df.iterrows():
            if pd.isna(row[0]):
            # Если значение равно None или nan, то пропускаем обработку строки
                result.append({
                "raw": None,
                "paragraph": int(row[1]),
                "type": None,
                "sentence_exercise": None,
                "object": None,
                "options": None,
                "answer": None,
                "description": None
                })
            else:
            
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
        

        # Если передан список exercise_types, то используем его для выбора упражнений
        if self.exercise_types is not None:
            function_names = [name for name in function_names if name in self.exercise_types]

        # Перемешиваем список, чтобы выбирать случайное упражнение
        random.shuffle(function_names)
        # Проходим по списку функций и проверяем условия для каждой
        for function_name in function_names:
            # Получаем условия для функции из словаря function_info
            conditions = function_info[function_name]['conditions']

            # Проверяем, выполняются ли условия для предложения

            if self.check_conditions(parsed_sentence, conditions, ex, function_name):
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

    def check_conditions(self, parsed_sentence, conditions, ex, function_name):

        for condition in conditions:
            attribute, value = condition
            if attribute in ['word', 'part_of_speech', 'sentence_member', 'lemma']:
                if not any(word[attribute] == value for word in parsed_sentence):
                    return False
            elif attribute == 'length':
                if len(parsed_sentence) <= value:
                    return False
            elif attribute == 'max_length':
                if len(parsed_sentence) >= value:
                    return False
            elif attribute == 'definition': # упростить лишние переменные из conditions
                pos, word = value
            # Проверяем, есть ли определение для заданного слова с заданной частью речи
                #word_list = [word['word'] for word in parsed_sentence if word['part_of_speech'] == pos]                              
                definition = None
                for word_dict in parsed_sentence:
                    if  word_dict['part_of_speech'] == pos:
                        definition = ex.get_definition(word_dict[word])
                        break
                if definition is None:
                    return False
            else:
                return False
        return True




def save_result_csv(result_df, path='exercise_ready/'):

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





class exercises:
    def __init__(self, df):
        self.df = df
        self.df = self.df.assign(options=None, type=None, sentence_exercise=None, object=None, answer=None, description=None)
     #забирать из ExercisesGeneration     
        self.function_description = {
            "missing_word": {
                "arguments": None,
                "returns": None,
                "description": "Напиши пропущенное слово",
                "conditions": [
                    ("part_of_speech", "NOUN"),
                    ("length", 5),
                    ("definition", ("NOUN", "word"))
                ]
            },
            "determiners": {
                "arguments": None,
                "returns": None,
                "description": """Выбери правильный определитель""",
                "conditions": [
                    ("part_of_speech", "DET"),
                    ("length", 4)
                ]
            },
            'missing_prepositions': {
                "arguments": None,
                "returns": None,
                "description": "Fill in the missing preposition",
                "conditions": [
                    ("part_of_speech", "ADP"),
                    ("length", 5)
                ]
            },
            'scrambled_words': {
                "arguments": None,
                "returns": None,
                "description": "Составьте слова в правильном порядке",
                "conditions": [
                    ("length", 4),
                    ("max_length", 9)
                ]
            }
        }

            

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
        """Вставь пропущенное слово"""
        self.sentence_dict = sentence_dict
        noun_list = [word for word in sentence_dict if word['part_of_speech'] == 'NOUN' and word['word'] != word[
            'word'].capitalize()]
        if noun_list:
            noun_choice = random.choice(noun_list)
            noun_word = noun_choice['word']
            options = None
            answer = noun_word
            definition = self.get_definition(noun_word)
            description = self.missing_word.__doc__ + ' его значение - ('  + definition +')'
            self.set_exercise(row_index, "missing_word", noun_word, options, answer, description)
            
            
    def missing_prepositions(self, row_index, sentence_dict):
        """Выбери пропущенный предлог"""
        self.sentence_dict = sentence_dict
        prepositions = {
            'Prepositions of time': ['after', 'before', 'during', 'since', 'until'],
            'Prepositions of place': ['above', 'across', 'around', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond', 'by', 'down', 'in', 'inside', 'near', 'off', 'on', 'onto', 'out', 'outside', 'over', 'past', 'through', 'throughout', 'under', 'underneath', 'up'],
            'Prepositions of direction or movement': ['across', 'along', 'around', 'down', 'into', 'off', 'onto','out of' , 'past' , 'through' , 'to' , 'toward' , 'up'],
        # Combine the groups into one group
            "Combined group": ['by' , 'with','by','from' , 'out of','of','with','as' , 'like','against' , 'except']
            }
        prepositions_list = [prep for group in prepositions.values() for prep in group]
    
    # Choose a preposition that is in the sentence
        preposition_choice = None
        for word in sentence_dict:
            if word['part_of_speech'] == "ADP" and word['word'] in prepositions_list:
                preposition_choice = word['word']
                break
    # If no preposition is found, return None
        if not preposition_choice:
            return None

    # Find the group that the chosen preposition belongs to
        preposition_group = None
        for group, preps in prepositions.items():
            if preposition_choice in preps:
                preposition_group = group
                break

    # Create options based on the group
        if preposition_group in ['Prepositions of place','Prepositions of direction or movement']:
            options = random.sample([prep for group, preps in prepositions.items() if group != preposition_group for prep in preps if prep != preposition_choice], 3)
        else:
            options = random.sample([prep for prep in prepositions[preposition_group] if prep != preposition_choice], 3)
    
        options.append(preposition_choice)
        random.shuffle(options)

        answer = preposition_choice
        description = self.missing_prepositions.__doc__
    # Use the set_exercise function to set the parameters in the dataframe, passing all necessary arguments
        self.set_exercise(row_index, "missing_prepositions", preposition_choice, options, answer, description)
        
    def scrambled_words(self, row_index, sentence_dict):
        # Создаем список слов для перемешивания
        words = [word['word'] for word in sentence_dict if word['part_of_speech'] != 'PUNCT']
        # Создаем копию списка слов для сохранения правильного порядка
        correct_order = words.copy()
        # Перемешиваем слова
        random.shuffle(words)
        # Создаем список слов предложения
        sentence_words = []
        for word in sentence_dict:
            if word['part_of_speech'] == 'PUNCT':
                sentence_words.append(word['word'])
            else:
                sentence_words.append('___')
        # Соединяем слова предложения в строку
        sentence_exercise = ' '.join(sentence_words)
        # Сохраняем результаты в датафрейме
        self.df.at[row_index, "type"] = "scrambled_words"
        self.df.at[row_index, "sentence_exercise"] = sentence_exercise
        self.df.at[row_index, "object"] = correct_order
        self.df.at[row_index, "options"] = words
        self.df.at[row_index, "answer"] = correct_order
        self.df.at[row_index, "description"] = "Составьте слова в правильном порядке"    

    def get_function_info(self):
        
        result = self.function_description
            
        return result  
    
    def get_definition(self, word):
        synsets = wordnet.synsets(word)
        if synsets:
            definition = synsets[0].definition()
            return definition
        else:
            return None



