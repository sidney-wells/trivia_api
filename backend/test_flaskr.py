import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_path = "postgres://{}:{}@{}/{}".format('postgres', 'localhost:5432', 'trivia_test')
        setup_db(self.app, self.database_path)
        
        self.new_question = {
            'question': 'ohhhh favorite pie',
            'answer': 'imagine pie', 
            'category': 3, 
            'difficulty': 2
        }
        
        self.incomplete_question = {
            'question': 'ohhhh favorite pie',
            'answer': 'imagine pie', 
            'category': 3
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_paginated_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['questions'])
       
    def test_404_sent_requesting_beyond_valid_page(self):
        res = self.client().get('/questions?page=1000')
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_422_if_question_does_not_post(self):
                
        res = self.client().post('/questions', json=self.incomplete_question)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')
    
    def test_405_if_question_creation_not_allowed(self):
        res = self.client().post('/questions/70', json=self.new_question)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'method not allowed')
    
    def test_get_questions_for_category(self):
        res = self.client().get('/categories/3/questions')
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        
        self.assertNotEqual(len(data['questions']), 0)
        self.assertEqual(data['current_category'], 'Geography')
     
    def test_400_failed_to_get_questions_for_category(self):
  
        res = self.client().get(f'/categories/1000/questions')
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'bad request')
    
    def test_delete_question(self):
        
        deleted_question = Question(question='capital of usa', answer='washington dc', category='4', difficulty=2)   
        deleted_question.insert()
        
        deleted_q_id = deleted_question.id    
        total_q_before_delete = Question.query.all()

        res = self.client().delete('/questions/{}'.format(deleted_q_id))
        data = json.loads(res.data)
    
        total_q_after_delete = Question.query.all()
        question = Question.query.filter(Question.id == 1).one_or_none()
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], deleted_q_id)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(total_q_before_delete) - len(total_q_after_delete) == 1)
        self.assertEqual(question, None)
     
    def test_create_new_question(self):
        res = self.client().post('/questions', json=self.new_question)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['created'])
        self.assertTrue(len(data['questions']))
    
    def test_get_question_search_with_results(self):
        res = self.client().post('/questions', json={'searchTerm': 'title'})
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), 2)
        self.assertTrue(data['total_questions'])
    
    def test_get_question_search_without_results(self):
        res = self.client().post('/questions', json={'searchTerm': 'yeeeetttt'})
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
    
    def test_get_quiz(self):
        
        parameters = {
            'previous_questions': [6, 7], 
            'quiz_category': {
                'type': 'Geogrpahy', 
                'id': '1'
                }
            }
        
        res = self.client().post('/quizzes', json=parameters)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])
        self.assertEqual(data['question']['category'], 1)
        self.assertNotEqual(data['question']['id'], 6)
        self.assertNotEqual(data['question']['id'], 7)

    def test_failed_to_get_quiz(self):
        response = self.client().post('/quizzes', json={})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()