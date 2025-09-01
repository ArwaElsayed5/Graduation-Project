from odoo import models, fields, api
import logging
from odoo.exceptions import UserError
import psycopg2
from datetime import datetime, timedelta
import pandas as pd
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.preprocessing import TransactionEncoder
from deap import base, creator, tools
from typing import List, Tuple
import random
import os

# Database configuration
DB_NAME = os.getenv("DB_NAME", "warehouse1_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", 5432)

# DEAP setup
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)
toolbox = base.Toolbox()

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

class SlottingWizard(models.TransientModel):
    _name = 'slotting.wizard'
    _description = 'Run Dynamic Slotting Optimization'

    timeframe = fields.Selection([
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('this_quarter', 'This Quarter')
    ], string='Timeframe')

    result = fields.Text(string='Optimization Result')

    def connect_db(self):
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM items")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        cursor.close()
        return connection

    def get_item_demand(self, timeframe):
        conn = self.connect_db()
        cursor = conn.cursor()
        if timeframe == 'last_week':
            last_week_start = datetime.now() - timedelta(days=7)
            query = f"""
                SELECT product_id, COUNT(*) AS demand 
                FROM Orders 
                WHERE date >= '{last_week_start.strftime('%Y-%m-%d')}' 
                AND date < '{(last_week_start + timedelta(days=7)).strftime('%Y-%m-%d')}'
                GROUP BY product_id;
            """
        elif timeframe == 'this_month':
            query = """
                SELECT product_id, COUNT(*) AS demand
                FROM Orders
                WHERE EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
                GROUP BY product_id;
            """
        elif timeframe == 'this_quarter':
            query = """
                SELECT product_id, COUNT(*) AS demand
                FROM Orders
                WHERE EXTRACT(QUARTER FROM date) = EXTRACT(QUARTER FROM CURRENT_DATE)
                GROUP BY product_id;
            """
        else:
            raise UserError(f"Invalid timeframe '{timeframe}'")

        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        print(f" Demand data for {timeframe}: {len(rows)} items")
        return {str(r[0]): r[1] for r in rows}

    def get_frequent_item_pairs(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT order_num, product_id FROM orders")
        rows = cur.fetchall()
        conn.close()

        df = pd.DataFrame(rows, columns=['order_num', 'product_id'])
        transactions = df.groupby('order_num')['product_id'].apply(list).tolist()
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

        freq_items = fpgrowth(df_encoded, min_support=0.02, use_colnames=True)
        if 'itemsets' not in freq_items.columns or freq_items.empty:
            return []

        freq_pairs = freq_items[freq_items['itemsets'].apply(lambda x: len(x) == 2)]
        return [tuple(sorted(list(item))) for item in freq_pairs['itemsets']]

    def get_address_data(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT address, types_of_storage, storage_capacity, proximity, slot_length_cm, slot_width_cm, slot_height_cm 
            FROM addresses
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_item_dimensions(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT item_id, length_cm, width_cm, height_cm FROM items")
        items = cur.fetchall()
        conn.close()
        return {item[0]: (item[1], item[2], item[3]) for item in items}

    def create_slot_pool(self, address_data):
        slot_pool = []
        for addr in address_data:
            name, storage_type, capacity, *_ = addr
            if storage_type == 'standard':
                capacity = 1
            for i in range(capacity):
                slot_pool.append((name, i))
        return slot_pool

    def create_individual(self, item_ids, slot_pool):
        return [random.randint(0, len(slot_pool) - 1) for _ in item_ids]

    def evaluate(self, individual, slot_pool, demand_data, address_proximity_map, address_dims_map, item_dims_map,
                 item_ids, frequent_pairs):
        fitness = 0
        proximity_map = {'near': 1, 'medium': 2, 'far': 3}
        item_to_slot = dict(zip(item_ids, individual))
        for item_id, slot_index in item_to_slot.items():
            demand = float(demand_data.get(str(item_id), 0))
            address_name, _ = slot_pool[slot_index]
            proximity = proximity_map.get(address_proximity_map.get(address_name, 'far'), 3)
            item_dims = item_dims_map.get(item_id)
            slot_dims = address_dims_map.get(address_name)
            if item_dims and slot_dims:
                item_volume = item_dims[0] * item_dims[1] * item_dims[2]
                slot_volume = slot_dims[0] * slot_dims[1] * slot_dims[2]
                if item_volume > slot_volume:
                    fitness -= 100
            if demand > 0:
                fitness += demand * (1 / (1 + proximity))
        for pair in frequent_pairs:
            item1, item2 = pair
            if item1 in item_ids and item2 in item_ids:
                idx1 = item_ids.index(item1)
                idx2 = item_ids.index(item2)
                slot_idx1 = individual[idx1]
                slot_idx2 = individual[idx2]
                address1, _ = slot_pool[slot_idx1]
                address2, _ = slot_pool[slot_idx2]
                if address1 == address2:
                    fitness += 10
        return fitness,

    def run_genetic_algorithm(self, demand_data):
        address_data = self.get_address_data()
        slot_pool = self.create_slot_pool(address_data)
        item_ids = list(demand_data.keys())
        num_items = len(item_ids)

        address_proximity_map = {addr[0]: addr[3] for addr in address_data}
        address_dims_map = {addr[0]: (addr[4], addr[5], addr[6]) for addr in address_data}
        item_dims_map = self.get_item_dimensions()
        frequent_pairs = self.get_frequent_item_pairs()

        toolbox.register("individual", tools.initIterate, creator.Individual,
                         lambda: self.create_individual(item_ids, slot_pool))
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutUniformInt, low=0, up=len(slot_pool) - 1, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)
        toolbox.register("evaluate", self.evaluate)

        population = toolbox.population(n=50)
        for ind in population:
            if not ind.fitness.valid:
                ind.fitness.values = toolbox.evaluate(ind, slot_pool, demand_data, address_proximity_map,
                                                     address_dims_map, item_dims_map, item_ids, frequent_pairs)
        for gen in range(100):
            offspring = toolbox.select(population, len(population))
            offspring = list(map(toolbox.clone, offspring))
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < 0.7:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values, child2.fitness.values
            for mutant in offspring:
                if random.random() < 0.2:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values
            for ind in offspring:
                if not ind.fitness.valid:
                    ind.fitness.values = toolbox.evaluate(ind, slot_pool, demand_data, address_proximity_map,
                                                         address_dims_map, item_dims_map, item_ids, frequent_pairs)
            population[:] = offspring

        best_ind = tools.selBest(population, 1)[0]
        fitness = self.evaluate(best_ind, slot_pool=slot_pool, demand_data=demand_data,
                                address_proximity_map=address_proximity_map, address_dims_map=address_dims_map,
                                item_dims_map=item_dims_map, frequent_pairs=frequent_pairs, item_ids=item_ids)
        return best_ind, fitness, slot_pool, item_ids

    def action_run_slotting(self):
        demand_data = self.get_item_demand(self.timeframe)
        result_text = f"Running optimization for timeframe: {self.timeframe}\nItems: {len(demand_data)}"
        print(" Run Optimization clicked - timeframe:", self.timeframe)

        # Check if the record exists before updating
        old_results = self.env['slotting.result'].search([('timeframe', '=', self.timeframe)])
        for result in old_results:
            if result.exists():  # Only update if the record still exists
                old_results.write({'active': False})
            else:
                _logger.warning(f"Slotting result with ID {result.id} has been deleted or does not exist.")

        best_individual, fitness_score, slot_pool, item_ids = self.run_genetic_algorithm(demand_data)
        fitness_score = fitness_score[0]
        item_ids = list(demand_data.keys())
        assignments = dict(zip(item_ids, best_individual))
        slot_pool = self.create_slot_pool(self.get_address_data())

        detailed_result = ""
        for item_id_str, slot_index in assignments.items():
            item_id = int(item_id_str)
            address_name, _ = slot_pool[slot_index]
            product = self.env['product.product'].browse(item_id)
            if product.exists():
                # Create the result entry if product exists
                self.env['slotting.result'].create({
                    'item_id': item_id,
                    'slot_id': address_name,
                    'score': fitness_score,
                    'timeframe': self.timeframe,
                })
                _logger.info(f"Creating Slotting Result for item_id: {item_id} and slot: {address_name}")
            else:
                _logger.warning(f"Product with ID {item_id} does not exist, skipping assignment.")

        self.result = result_text + "\n\n" + detailed_result
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'slotting.result',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
