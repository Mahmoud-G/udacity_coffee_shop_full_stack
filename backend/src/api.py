import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from cerberus import Validator
from sqlalchemy.exc import IntegrityError

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''

# db_drop_and_create_all()

## ROUTES
'''
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks')
def retrieve_drinks():
    query = Drink.query.order_by(Drink.title).all()
    if query is None:
        abort(404)

    return jsonify({
        'success': True,
        'drinks': [item.short() for item in query]
    })
'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail')
def retrieve_drinks_detail():
    query = Drink.query.order_by(Drink.title).all()
    if query is None:
        abort(404)

    return jsonify({
        'success': True,
        'drinks': [item.long() for item in query]
    })

'''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['POST'])
def create_drink():
    body = request.get_json()

    try:
        schema = {
                "title": {
                    "type": "string",
                },
                "recipe": {
                            "type": "dict",
                            "schema": {
                                        "color": {
                                                "type": "string",
                                                'required': True,
                                                'minlength': 1
                                                },
                                        "name": {
                                                "type": "string",
                                                'required': True,
                                                'minlength': 1
                                                },
                                        "parts": {
                                                "type": "integer",
                                                'minlength': 1
                                                # "min": 1,
                                                # "max": 4094
                                                },
                                        }
                           },

                }

        v = Validator(schema)
        request_data = {'recipe': body.get('recipe', None), 'title': body.get('title', None)}
        if v.validate(request_data):
            query = Drink(title=request_data['title'], recipe=json.dumps(request_data['recipe']))
            query.insert()

            return jsonify({
                'success': True,
                'drinks': query.long()
            })
        else:
            abort(400)

    except IntegrityError:
        abort(422, {'message': f'This Drink already exist'})

    except Exception as e:
        print(e)

        abort(422, {'message': v.errors})

#     PATCH /drinks/<id>
#         where <id> is the existing model id
#         it should respond with a 404 error if <id> is not found
#         it should update the corresponding row for <id>
#         it should require the 'patch:drinks' permission
#         it should contain the drink.long() data representation
#     returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
#         or appropriate status code indicating reason for failure


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
def patch_drink(drink_id):
    body = request.get_json()
    query = Drink.query.filter(Drink.id == drink_id).one_or_none()

    if query is None:
        abort(404)

    try:
        schema = {
                "title": {
                    "type": "string",
                },
                "recipe": {
                            "type": "dict",
                            "schema": {
                                        "color": {
                                                "type": "string",
                                                'required': True,
                                                'minlength': 1
                                                },
                                        "name": {
                                                "type": "string",
                                                'required': True,
                                                'minlength': 1
                                                },
                                        "parts": {
                                                "type": "integer",
                                                'minlength': 1
                                                # "min": 1,
                                                # "max": 4094
                                                },
                                        }
                           },

                }

        v = Validator(schema)
        request_data = {'recipe': body.get('recipe', None), 'title': body.get('title', None)}
        new_title = request_data['title']
        new_recipe = request_data['recipe']
        if v.validate(request_data):
            if new_title or new_recipe:
                if new_title:
                    query.title = new_title
                if new_recipe:
                    # query.recipe = str(request_data['recipe']).replace("'",'"')
                    query.recipe = json.dumps(new_recipe)

                query.update()
            else:
                abort(400)

            return jsonify({
                'success': True,
                'drinks': query.long()
            })
        else:
            abort(400)

    except Exception as e:
        print(e)

        abort(422, {'message': v.errors})


'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
def delete_drink(drink_id):
    query = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if query is None:
        abort(404)

    try:
        query.delete()

        return jsonify({
            'success': True,
            'delete': drink_id
        })

    except:
        abort(422)


## Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    message = 'unprocessable.'
    try:
        message = error.description['message']
    except Exception as e:
        print(e)
    return jsonify({
        'success': False,
        'error': 422,
        'message': message
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 405,
        'message': 'method not allowed.'
    }), 405


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request."
    }), 400


'''
@TODO implement error handler for 404
    error handler should conform to general task above 
'''


@app.errorhandler(404)
def not_fount(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'resource not found.'
    }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above 
'''


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': 'Unauthorized.'
    }), 401
