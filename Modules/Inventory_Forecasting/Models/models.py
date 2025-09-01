from odoo import models, fields, api
import logging
import os
import pandas as pd
from pycaret.regression import load_model, predict_model
import joblib  # or import load_model if using the pycaret package

_logger = logging.getLogger(__name__)


class SalesPrediction(models.TransientModel):
    _name = 'inventory.slotting.prediction'
    _description = 'Sales Prediction'

    item_id = fields.Integer(string='Item ID', required=True)
    shop_id = fields.Integer(string='Shop ID', required=True)
    predicted_sales = fields.Float(string='Predicted Weekly Sales', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Predicted')
    ], default='draft', string='Status')

    def action_predict(self):
        self.ensure_one()
        try:
            # Correctly form the model and data paths
            module_path = os.path.dirname(os.path.dirname(__file__))
            model_path = os.path.join(module_path,
                                      'sales_forecast_model.pkl')  # Use os.path.join for safe file path handling
            data_path = os.path.join(module_path, 'sales-preprocessed.csv')

            # Check if the model path exists before trying to load the model
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")

            # Ensure we load the correct model (e.g., joblib for sklearn models, or the appropriate method)
            model = joblib.load(model_path)  # If using joblib for sklearn model, adjust accordingly if using pycaret

            # Check if data file exists
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Data file not found at {data_path}")

            df = pd.read_csv(data_path)

            # Filter the data for the correct item and shop
            history = df[(df['item_id'] == self.item_id) & (df['shop_id'] == self.shop_id)].sort_values(
                by=['year', 'week'])

            if history.empty:
                raise ValueError('No historical data found for this item and shop combination.')

            # Prepare the input row for the model
            latest_row = history.iloc[-1:].copy()
            input_row = {
                'itemID': self.item_id,
                'shopID': self.shop_id,
                'lag1': latest_row['weekly_sales'].values[0],
                'lag2': latest_row['lag_1'].values[0],
                'lag3': latest_row['lag_2'].values[0],
                'lag4': latest_row['lag_3'].values[0],
                'rollingMean4': latest_row['rolling_mean_4'].values[0],
                'salesDiff1': latest_row['weekly_sales'].values[0] - latest_row['lag_1'].values[0]
                if pd.notna(latest_row['lag_1'].values[0]) else 0
            }

            input_df = pd.DataFrame([input_row])

            # Predict using the model
            prediction = predict_model(model, data=input_df)

            # Update the record with the predicted sales value
            self.write({
                'predicted_sales': prediction['prediction_label'].values[0],
                'state': 'done'
            })

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'inventory.slotting.prediction',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'current',
                'context': {'form_view_initial_mode': 'readonly'},
            }

        except Exception as e:
            raise models.UserError(str(e))

    def action_reset(self):
        self.write({
            'predicted_sales': 0.0,
            'state': 'draft'
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'inventory.slotting.prediction',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }