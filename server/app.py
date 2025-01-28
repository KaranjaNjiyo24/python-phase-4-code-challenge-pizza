#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

class RestaurantsList(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return [
            {
                'id': restaurant.id,
                'name': restaurant.name,
                'address': restaurant.address
            }
            for restaurant in restaurants
        ], 200

class RestaurantDetail(Resource):
    def get(self, id):
        restaurant = db.session.get(Restaurant, id)
        if restaurant:
            return restaurant.to_dict(rules=('-pizzas',)), 200
        else:
            return {"error": "Restaurant not found"}, 404
        
    def delete(self, id):
        restaurant = db.session.get(Restaurant, id)
        if restaurant:
            try:
                db.session.delete(restaurant)
                db.session.commit()
                return '', 204
            except Exception:
                db.session.rollback()
                return {"error": "Failed to delete restaurant"}, 500
        else:
            return {"error": "Restaurant not found"}, 404

class PizzasList(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        # Excluding restaurant_pizzas from serialization
        return [
            {
                'id': pizza.id,
                'name': pizza.name,
                'ingredients': pizza.ingredients
            }
            for pizza in pizzas
        ], 200
    
class RestaurantPizzasList(Resource):
    def post(self):
        data = request.get_json()

        # Extracting our data
        price = data.get('price')
        pizza_id = data.get('pizza_id')
        restaurant_id = data.get('restaurant_id')

        # Validating presence of fields
        if price is None or pizza_id is None or restaurant_id is None:
            return {"errors": ["Missing required fields"]}, 400

        # Validating the price
        if not isinstance(price, int) or not (1 <= price <= 30):
            return {"errors": ["validation errors"]}, 400

        # Validating pizza and restaurant that they exist
        pizza = db.session.get(Pizza, pizza_id)
        restaurant = db.session.get(Restaurant, restaurant_id)

        if not pizza or not restaurant:
            return {"errors": ["Pizza or Restaurant not found"]}, 400

        # Create RestaurantPizza
        try:
            restaurant_pizza = RestaurantPizza(
                price=price,
                pizza_id=pizza_id,
                restaurant_id=restaurant_id
            )
            db.session.add(restaurant_pizza)
            db.session.commit()
            return restaurant_pizza.to_dict(rules=(
                '-pizza.restaurant_pizzas',
                '-restaurant.restaurant_pizzas'
            )), 201
        except Exception as e:
            db.session.rollback()
            return {"errors": ["validation errors"]}, 400
        
api.add_resource(RestaurantsList, '/restaurants')
api.add_resource(RestaurantDetail, '/restaurants/<int:id>')
api.add_resource(PizzasList, '/pizzas')
api.add_resource(RestaurantPizzasList, '/restaurant_pizzas')
    
@app.route("/")
def index():
    return "<h1>Pizza challenge API</h1>"


if __name__ == "__main__":
    app.run(port=5555, debug=True)
