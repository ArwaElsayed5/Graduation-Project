# AI-Powered Inventory Management & Dynamic Slotting in Odoo

# Project Overview
This project enhances traditional inventory management in Odoo by implementing **AI-powered demand forecasting** and a **dynamic slotting optimizer**. The goal is to reduce stockouts, improve picking efficiency, and optimize warehouse operations.

---

# Problem
Traditional inventory management in Odoo lacked:
- Accurate demand forecasting
- Efficient slotting
This led to frequent stockouts and increased picker travel time.

---

# Approach
- Implemented **AI-powered demand forecasting** using Linear Regression with engineered time-series features (lag values, rolling averages, sales differences).  
- Designed a **Genetic Algorithm-based slotting optimizer** that allocates products to warehouse slots based on:
  - Demand frequency  
  - Item compatibility  
  - Product dimensions  
  - Proximity to dispatch zones  
- Integrated forecasting and slotting models into Odoo as custom modules with automated workflows.  
- Built and tested module functionalities using **Katalon Studio** for reliability and accuracy.  
- Compared algorithms with alternative ML and metaheuristic approaches to select the best-performing methods before deployment.


# Results
- Improved forecast accuracy compared to baseline methods, with Linear Regression outperforming other ML algorithms.  
- Optimized slotting significantly reduced average picker travel distance across multiple warehouse sizes.


# Tools & Technologies
- **Programming & Analysis:** Python, scikit-learn, pandas  
- **Database & ERP:** Odoo, PostgreSQL  
- **Algorithms:** Linear Regression, Genetic Algorithm, FPGrowth  
- **IDE & Testing:** PyCharm, Katalon Studio  

