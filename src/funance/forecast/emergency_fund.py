import os

import pandas as pd


def get_runway_report(spec: dict) -> dict:
    runway_goal_mos = spec['runway_goal_mos']
    monthly_spending_assumption = spec['monthly_spending_assumption']
    df = pd.DataFrame(spec['sources'])
    amt_actual = df['value'].sum()
    amt_goal = runway_goal_mos * monthly_spending_assumption
    runway_mos = amt_actual/monthly_spending_assumption
    return {
        'df': df,
        'runway_mos_goal': runway_goal_mos,
        'runway_mos_actual': runway_mos,
        'amt_goal': amt_goal,
        'amt_actual': amt_actual
    }
