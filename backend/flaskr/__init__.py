import os
from flask import Flask, request, abort, jsonify, flash, json
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE
  
  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  app = Flask(__name__)
  setup_db(app)
  CORS(app, resources={'/': {'origins': '*'}})
  
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response; 
  
  @app.route('/categories', methods=['GET'])
  def get_categories():
    all_categories = Category.query.all()
    categories = {}
    for category in all_categories:
      categories[category.id] = category.type 
    
    if len(categories) == 0:
      abort(404)
          
    return jsonify({
      'success': True,
      'categories': categories
    })

  @app.route('/questions')
  def get_questions(): 

    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)  
    
    if len(current_questions) == 0:
      abort(404)
      
    all_categories = Category.query.all()
    categories = {}
    for category in all_categories:
      categories[category.id] = category.type 
    
    return jsonify({
      'success': True,
      'questions': current_questions, 
      'total_questions': len(Question.query.all()),
      'categories': categories
    })
    
  @app.route('/categories/<int:category_id>/questions')
  def get_questions_for_category(category_id):    
    selection = Question.query.filter(Question.category == category_id).all()
    questions = [question.format() for question in selection]
    category = Category.query.filter_by(id=category_id).one_or_none()
    if (category is None):
      abort(400)
    current_category = category.format()['type']
    if len(questions) == 0:
        abort(404)
    return jsonify({
        'success': True,
        'questions': questions,
        'total_question': len(questions),
        'current_category': current_category
    })

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):

    try: 
      question = Question.query.filter(Question.id == question_id).one_or_none()
      if question is None: 
        abort(422)
      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True, 
        'deleted': question.id, 
        'questions': current_questions, 
        'total_questions': len(Question.query.all())
      })
    except(): 
      abort(422)

  @app.route('/questions', methods=['POST'])
  def create_question(): 
    body = request.get_json()
    if (body.get('searchTerm')): 
      search = body.get('searchTerm', None)
      
      selection = Question.query.order_by(Question.id).filter(Question.question.ilike(f'%{search}%')).all()
      
      if (len(selection) == 0):
        abort(404)
        
      current_questions = paginate_questions(request, selection)
      
      return jsonify({
        'success': True, 
        'questions': current_questions, 
        'total_questions': len(Question.query.all())
      })
    else:
      new_question = body.get('question', None)
      new_answer = body.get('answer', None)
      category = body.get('category', None)
      difficulty_score = body.get('difficulty', None)
      
      if ((new_question is None) or (new_answer is None) or (difficulty_score is None) or (category is None)):
        abort(422)
        
      try: 
        question = Question(question=new_question, answer=new_answer, category=category, difficulty=difficulty_score)
        question.insert()
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)   
          
        return jsonify({
            'success': True, 
            'created': question.id, 
            'question_created': question.question,
            'questions': current_questions, 
            'total_questions': len(Question.query.all())
          })
      except(): 
        abort(422) 

  @app.route('/quizzes', methods=['POST'])
  def get_quiz():
        
    if request.data:
          
      search_key = json.loads(request.data.decode('utf-8'))
      
      if (('quiz_category' in search_key and 'id' in search_key['quiz_category']) and 'previous_questions' in search_key):
        
        questions_query = []
              
        if (search_key['quiz_category']['id'] == 0):
          questions_query = Question.query.all()
        else:
          questions_query = Question.query.filter_by(category=search_key['quiz_category']['id']).filter(Question.id.notin_(search_key["previous_questions"])).all()
              
        length_of_available_question = len(questions_query)
        
        if length_of_available_question > 0:
          result = {
            "success": True,
            "question": Question.format(questions_query[random.randrange(0, length_of_available_question)])
            }
        else:
          result = {
            "success": True,
            "question": None
          }
        return jsonify(result)
      else: 
        abort(404)
    else:
      abort(422)
  
  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
        "success": False, 
        'error': 404, 
        'message': "resource not found"
      }), 404
      
  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
        "success": False, 
        'error': 422, 
        'message': "unprocessable"
      }), 422
      
  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
        "success": False, 
        'error': 400, 
        'message': "bad request"
      }), 400
      
  @app.errorhandler(405)
  def not_found(error):
      return jsonify({
        "success": False, 
        'error': 405, 
        'message': "method not allowed"
      }), 405
  
  return app

    