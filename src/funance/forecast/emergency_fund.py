import os

import pandas as pd


def get_runway_report(spec: dict) -> dict:
    df = pd.DataFrame(spec['sources'])
    total_funds = df['value'].sum()
    runway_goal_mos = spec['runway_goal_mos']
    monthly_spending_assumption = spec['monthly_spending_assumption']
    runway_mos = total_funds/monthly_spending_assumption
    return {
        'df': df,
        'goal': runway_goal_mos,
        'actual': runway_mos
    }
