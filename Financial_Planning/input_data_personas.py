"""
Persona-based sample inputs for Financial Planning workflow.

Usage:
- Import `client_profiles` to access all personas.
- Import `client_data` for a single default persona.
"""

client_profiles = {
    "tier2_single_income_home_loan": {
        'client_data': {
            'name': 'Ritesh Kumar',
            'pan': '',
            'organization_name': 'Manufacturing Pvt Ltd',
            'date_of_birth': '1990-04-12',
            'spouse_name': 'Pooja',
            'spouse_dob': '1993-09-30',
            'if_any_kids': True,
            'children': [
                {'child_name': 'Aarav', 'child_dob': '2016-03-18', 'Gender': 'Male', 'investments': []}
            ],
            'retirement_age': 55
        },
        'investment_details': {
            'financial_summary': [
                {
                    'monthly_salary': 85000,
                    'monthly_expenses_excl_emis': 42000,
                    'other_income(rental/interest/other)': 1500,
                    'lump_sum_available': 120000,
                    'miscellaneous_kids_education_expenses_monthly': 4000,
                    'annual_vacation_expenses': 30000,
                    'emergency_fund_maintained': 160000
                }
            ],
            'real_estate_investment': [
                {'current_market_value': 5200000, 'rental_income': 0}
            ],
            'retirement_investments': {
                'epf': [
                    {'current_value': 650000, 'employee_employer_contribution_monthly': 9000, 'interest_rate': 0.085}
                ],
                'ppf': [
                    {'current_value': 180000, 'annual_contribution': 30000, 'interest_rate': 0.075}
                ],
                'nps': []
            },
            'bonds': [],
            'mutual_funds': [
                {'current_value': 320000, 'expected_annual_return': 0.12, 'sip_amount': 8000}
            ],
            'direct_equity': [
                {'portfolio_value': 75000}
            ],
            'reits': [{'current_value': 0}],
            'pms_aif': [{'current_value': 0}],
            'esops': [{'vested_esops_value': 0, 'unvested_esops_value': 0}],
            'fixed_deposits': [
                {'name_of_bank': 'state_bank_of_india', 'principal_amount': 200000, 'interest_rate': 0.065, 'maturity_date': '11-2029'}
            ],
            'other_investments': []
        },
        'financial_goals': [
            {'goal_name': 'Family Car Upgrade', 'capital_required_today': 800000, 'target_year': 2029},
            {'goal_name': 'Aarav Marriage', 'capital_required_today': 1000000, 'target_year': 2042}
        ],
        'liabilities': [
            {
                'type': 'Home loan',
                'outstanding_balance': 2800000,
                'interest_rate': 0.089,
                'emi_amount': 28000,
                'is_under_penalty_period': False,
                'time_left_to_come_out_of_penalty_period(months)': 0
            },
            {
                'type': 'Bike loan',
                'outstanding_balance': 70000,
                'interest_rate': 0.105,
                'emi_amount': 3200,
                'is_under_penalty_period': False,
                'time_left_to_come_out_of_penalty_period(months)': 0
            }
        ],
        'education_planning': [
            {
                'name_of_kid': 'Aarav',
                'dob': '2016-03-18',
                'graduation_stream': 'B.Tech',
                'graduation_destination': 'Domestic',
                'fund_allocated_for_graduation': 0,
                'post_graduation_stream': 'MBA',
                'post_graduation_destination': 'Domestic',
                'scheme_for_education': []
            }
        ],
        'life_insurance': []
    },

    "dual_income_urban_two_kids_ssy_esop": {
        'client_data': {
            'name': 'Neeraj Sharma',
            'pan': '',
            'organization_name': 'Product Tech India',
            'date_of_birth': '1989-10-25',
            'spouse_name': 'Kritika',
            'spouse_dob': '1991-06-14',
            'if_any_kids': True,
            'children': [
                {'child_name': 'Anaya', 'child_dob': '2015-01-09', 'Gender': 'Female', 'investments': [
                    {'type': 'SUKANYA SAMRIDDHI YOJANA', 'commencement_date': '2016-04-01', 'annual_contribution': 75000, 'current_value': 620000}
                ]},
                {'child_name': 'Vivaan', 'child_dob': '2019-08-27', 'Gender': 'Male', 'investments': []}
            ],
            'retirement_age': 57
        },
        'investment_details': {
            'financial_summary': [
                {
                    'monthly_salary': 245000,
                    'monthly_expenses_excl_emis': 128000,
                    'other_income(rental/interest/other)': 7000,
                    'lump_sum_available': 450000,
                    'miscellaneous_kids_education_expenses_monthly': 12000,
                    'annual_vacation_expenses': 100000,
                    'emergency_fund_maintained': 750000
                }
            ],
            'real_estate_investment': [
                {'current_market_value': 9800000, 'rental_income': 15000}
            ],
            'retirement_investments': {
                'epf': [
                    {'current_value': 1850000, 'employee_employer_contribution_monthly': 24000, 'interest_rate': 0.085}
                ],
                'ppf': [
                    {'current_value': 420000, 'annual_contribution': 50000, 'interest_rate': 0.075}
                ],
                'nps': []
            },
            'bonds': [],
            'mutual_funds': [
                {'current_value': 2100000, 'expected_annual_return': 0.12, 'sip_amount': 35000}
            ],
            'direct_equity': [{'portfolio_value': 450000}],
            'reits': [{'current_value': 60000}],
            'pms_aif': [{'current_value': 0}],
            'esops': [{'vested_esops_value': 450000, 'unvested_esops_value': 900000}],
            'fixed_deposits': [
                {'name_of_bank': 'hdfc_bank', 'principal_amount': 350000, 'interest_rate': 0.068, 'maturity_date': '08-2031'}
            ],
            'other_investments': []
        },
        'financial_goals': [
            {'goal_name': 'Bigger Home Down Payment', 'capital_required_today': 2500000, 'target_year': 2030},
            {'goal_name': 'International Family Trip', 'capital_required_today': 600000, 'target_year': 2028}
        ],
        'liabilities': [
            {
                'type': 'Home loan',
                'outstanding_balance': 4100000,
                'interest_rate': 0.086,
                'emi_amount': 43000,
                'is_under_penalty_period': False,
                'time_left_to_come_out_of_penalty_period(months)': 0
            },
            {
                'type': 'Car loan',
                'outstanding_balance': 460000,
                'interest_rate': 0.092,
                'emi_amount': 12500,
                'is_under_penalty_period': False,
                'time_left_to_come_out_of_penalty_period(months)': 0
            }
        ],
        'education_planning': [
            {
                'name_of_kid': 'Anaya',
                'dob': '2015-01-09',
                'graduation_stream': 'B.Tech',
                'graduation_destination': 'Domestic',
                'fund_allocated_for_graduation': 0,
                'post_graduation_stream': 'MBA',
                'post_graduation_destination': 'International',
                'scheme_for_education': []
            },
            {
                'name_of_kid': 'Vivaan',
                'dob': '2019-08-27',
                'graduation_stream': 'MBBS',
                'graduation_destination': 'Domestic',
                'fund_allocated_for_graduation': 0,
                'post_graduation_stream': 'NA',
                'post_graduation_destination': 'NA',
                'scheme_for_education': []
            }
        ],
        'life_insurance': []
    },

    "single_mother_salaried_two_kids": {
        'client_data': {
            'name': 'Swati Joshi',
            'pan': '',
            'organization_name': 'Pharma Solutions Ltd',
            'date_of_birth': '1988-07-04',
            'spouse_name': '',
            'spouse_dob': '',
            'if_any_kids': True,
            'children': [
                {'child_name': 'Ishita', 'child_dob': '2013-12-12', 'Gender': 'Female', 'investments': [
                    {'type': 'SUKANYA SAMRIDDHI YOJANA', 'commencement_date': '2015-01-01', 'annual_contribution': 60000, 'current_value': 540000}
                ]},
                {'child_name': 'Kabir', 'child_dob': '2018-05-20', 'Gender': 'Male', 'investments': []}
            ],
            'retirement_age': 60
        },
        'investment_details': {
            'financial_summary': [
                {
                    'monthly_salary': 135000,
                    'monthly_expenses_excl_emis': 79000,
                    'other_income(rental/interest/other)': 2000,
                    'lump_sum_available': 90000,
                    'miscellaneous_kids_education_expenses_monthly': 9000,
                    'annual_vacation_expenses': 45000,
                    'emergency_fund_maintained': 400000
                }
            ],
            'real_estate_investment': [
                {'current_market_value': 0, 'rental_income': 0}
            ],
            'retirement_investments': {
                'epf': [
                    {'current_value': 1120000, 'employee_employer_contribution_monthly': 14000, 'interest_rate': 0.085}
                ],
                'ppf': [
                    {'current_value': 260000, 'annual_contribution': 30000, 'interest_rate': 0.075}
                ],
                'nps': []
            },
            'bonds': [],
            'mutual_funds': [
                {'current_value': 780000, 'expected_annual_return': 0.12, 'sip_amount': 12000}
            ],
            'direct_equity': [{'portfolio_value': 60000}],
            'reits': [{'current_value': 0}],
            'pms_aif': [{'current_value': 0}],
            'esops': [{'vested_esops_value': 0, 'unvested_esops_value': 0}],
            'fixed_deposits': [
                {'name_of_bank': 'icici_bank', 'principal_amount': 150000, 'interest_rate': 0.067, 'maturity_date': '02-2028'}
            ],
            'other_investments': []
        },
        'financial_goals': [
            {'goal_name': 'Emergency House Renovation', 'capital_required_today': 500000, 'target_year': 2027}
        ],
        'liabilities': [
            {
                'type': 'Personal loan',
                'outstanding_balance': 320000,
                'interest_rate': 0.132,
                'emi_amount': 9800,
                'is_under_penalty_period': False,
                'time_left_to_come_out_of_penalty_period(months)': 0
            }
        ],
        'education_planning': [
            {
                'name_of_kid': 'Ishita',
                'dob': '2013-12-12',
                'graduation_stream': 'MBBS',
                'graduation_destination': 'Domestic',
                'fund_allocated_for_graduation': 0,
                'post_graduation_stream': 'NA',
                'post_graduation_destination': 'NA',
                'scheme_for_education': []
            },
            {
                'name_of_kid': 'Kabir',
                'dob': '2018-05-20',
                'graduation_stream': 'B.Tech',
                'graduation_destination': 'Domestic',
                'fund_allocated_for_graduation': 0,
                'post_graduation_stream': 'NA',
                'post_graduation_destination': 'NA',
                'scheme_for_education': []
            }
        ],
        'life_insurance': []
    },

    "dink_metro_aggressive_investing": {
        'client_data': {
            'name': 'Kunal Batra',
            'pan': '',
            'organization_name': 'SaaS Startup',
            'date_of_birth': '1993-02-18',
            'spouse_name': 'Rhea',
            'spouse_dob': '1994-10-05',
            'if_any_kids': False,
            'children': [],
            'retirement_age': 55
        },
        'investment_details': {
            'financial_summary': [
                {
                    'monthly_salary': 220000,
                    'monthly_expenses_excl_emis': 95000,
                    'other_income(rental/interest/other)': 5000,
                    'lump_sum_available': 600000,
                    'miscellaneous_kids_education_expenses_monthly': 0,
                    'annual_vacation_expenses': 150000,
                    'emergency_fund_maintained': 800000
                }
            ],
            'real_estate_investment': [
                {'current_market_value': 0, 'rental_income': 0}
            ],
            'retirement_investments': {
                'epf': [
                    {'current_value': 950000, 'employee_employer_contribution_monthly': 12000, 'interest_rate': 0.085}
                ],
                'ppf': [
                    {'current_value': 150000, 'annual_contribution': 20000, 'interest_rate': 0.075}
                ],
                'nps': [],
                'ulip': [
                    {
                            'policy_name': 'Sample ULIP',
                            'commencement_date': '15-06-2020',
                            'ppt': 10,
                            'term': 15,
                            'premium': 100000,
                            'maturity_value': 1500000,
                            'maturity_year': 2035
                    }
                ]
            },
            'bonds': [],
            'mutual_funds': [
                {'current_value': 2600000, 'expected_annual_return': 0.12, 'sip_amount': 50000}
            ],
            'direct_equity': [{'portfolio_value': 980000}],
            'reits': [{'current_value': 125000}],
            'pms_aif': [{'current_value': 350000}],
            'esops': [{'vested_esops_value': 300000, 'unvested_esops_value': 1200000}],
            'fixed_deposits': [
                {'name_of_bank': 'axis_bank', 'principal_amount': 200000, 'interest_rate': 0.067, 'maturity_date': '10-2027'}
            ],
            'other_investments': []
        },
        'financial_goals': [
            {'goal_name': 'World Tour', 'capital_required_today': 1800000, 'target_year': 2030},
            {'goal_name': 'Second Home', 'capital_required_today': 4500000, 'target_year': 2034}
        ],
        'liabilities': [
            {
                'type': 'Car loan',
                'outstanding_balance': 550000,
                'interest_rate': 0.091,
                'emi_amount': 15500,
                'is_under_penalty_period': False,
                'time_left_to_come_out_of_penalty_period(months)': 0
            }
        ],
        'education_planning': [],
        'life_insurance': []
    },

    "self_employed_variable_income_family": {
        'client_data': {
            'name': 'Imran Shaikh',
            'pan': '',
            'organization_name': 'Shaikh Traders',
            'date_of_birth': '1987-11-03',
            'spouse_name': 'Sana',
            'spouse_dob': '1990-02-10',
            'if_any_kids': True,
            'children': [
                {'child_name': 'Rehan', 'child_dob': '2012-06-21', 'Gender': 'Male', 'investments': []}
            ],
            'retirement_age': 60
        },
        'investment_details': {
            'financial_summary': [
                {
                    'monthly_salary': 160000,
                    'monthly_expenses_excl_emis': 90000,
                    'other_income(rental/interest/other)': 12000,
                    'lump_sum_available': 250000,
                    'miscellaneous_kids_education_expenses_monthly': 6000,
                    'annual_vacation_expenses': 50000,
                    'emergency_fund_maintained': 300000
                }
            ],
            'real_estate_investment': [
                {'current_market_value': 6800000, 'rental_income': 18000}
            ],
            'retirement_investments': {
                'epf': [],
                'ppf': [
                    {'current_value': 500000, 'annual_contribution': 50000, 'interest_rate': 0.075}
                ],
                'nps': []
            },
            'bonds': [],
            'mutual_funds': [
                {'current_value': 900000, 'expected_annual_return': 0.12, 'sip_amount': 15000}
            ],
            'direct_equity': [{'portfolio_value': 140000}],
            'reits': [{'current_value': 0}],
            'pms_aif': [{'current_value': 0}],
            'esops': [{'vested_esops_value': 0, 'unvested_esops_value': 0}],
            'fixed_deposits': [
                {'name_of_bank': 'bank_of_baroda', 'principal_amount': 450000, 'interest_rate': 0.069, 'maturity_date': '01-2030'}
            ],
            'other_investments': []
        },
        'financial_goals': [
            {'goal_name': 'Business Expansion Reserve', 'capital_required_today': 2000000, 'target_year': 2029},
            {'goal_name': 'Family Pilgrimage', 'capital_required_today': 350000, 'target_year': 2028}
        ],
        'liabilities': [
            {
                'type': 'Business loan',
                'outstanding_balance': 900000,
                'interest_rate': 0.118,
                'emi_amount': 24000,
                'is_under_penalty_period': True,
                'time_left_to_come_out_of_penalty_period(months)': 8
            }
        ],
        'education_planning': [
            {
                'name_of_kid': 'Rehan',
                'dob': '2012-06-21',
                'graduation_stream': 'MBBS',
                'graduation_destination': 'Domestic',
                'fund_allocated_for_graduation': 0,
                'post_graduation_stream': 'MBA',
                'post_graduation_destination': 'Domestic',
                'scheme_for_education': []
            }
        ],
        'life_insurance': []
    },

    "pre_retirement_conservative_couple": {
        'client_data': {
            'name': 'Madhukar Iyer',
            'pan': '',
            'organization_name': 'Logistics India Ltd',
            'date_of_birth': '1976-01-15',
            'spouse_name': 'Latha',
            'spouse_dob': '1979-03-02',
            'if_any_kids': True,
            'children': [
                {'child_name': 'Nikhil', 'child_dob': '2010-09-14', 'Gender': 'Male', 'investments': []}
            ],
            'retirement_age': 60
        },
        'investment_details': {
            'financial_summary': [
                {
                    'monthly_salary': 175000,
                    'monthly_expenses_excl_emis': 98000,
                    'other_income(rental/interest/other)': 9000,
                    'lump_sum_available': 700000,
                    'miscellaneous_kids_education_expenses_monthly': 3000,
                    'annual_vacation_expenses': 60000,
                    'emergency_fund_maintained': 1200000
                }
            ],
            'real_estate_investment': [
                {'current_market_value': 12500000, 'rental_income': 20000}
            ],
            'retirement_investments': {
                'epf': [
                    {'current_value': 3600000, 'employee_employer_contribution_monthly': 26000, 'interest_rate': 0.085}
                ],
                'ppf': [
                    {'current_value': 1200000, 'annual_contribution': 0, 'interest_rate': 0.075}
                ],
                'nps': []
            },
            'bonds': [],
            'mutual_funds': [
                {'current_value': 1450000, 'sip_amount': 12000}
            ],
            'direct_equity': [{'portfolio_value': 220000}],
            'reits': [{'current_value': 0}],
            'pms_aif': [{'current_value': 0}],
            'esops': [{'vested_esops_value': 0, 'unvested_esops_value': 0}],
            'fixed_deposits': [
                {'name_of_bank': 'state_bank_of_india', 'principal_amount': 1500000, 'interest_rate': 0.068, 'maturity_date': '06-2028'}
            ],
            'other_investments': []
        },
        'financial_goals': [
            {'goal_name': 'Retirement Travel Fund', 'capital_required_today': 1000000, 'target_year': 2032},
            {'goal_name': 'Nikhil Marriage', 'capital_required_today': 1800000, 'target_year': 2035}
        ],
        'liabilities': [
            {
                'type': 'Home loan',
                'outstanding_balance': 850000,
                'interest_rate': 0.087,
                'emi_amount': 22000,
                'is_under_penalty_period': False,
                'time_left_to_come_out_of_penalty_period(months)': 0
            }
        ],
        'education_planning': [
            {
                'name_of_kid': 'Nikhil',
                'dob': '2010-09-14',
                'graduation_stream': 'B.Tech',
                'graduation_destination': 'Domestic',
                'post_graduation_stream': 'NA',
                'post_graduation_destination': 'NA',
                'scheme_for_education': []
            }
        ],
        'life_insurance': []
    },

    "late_retirement_loan_case_family": {
        'client_data': {
            'name': 'Vikram Desai',
            'pan': '',
            'organization_name': 'Infrastructure Corp Ltd',
            'date_of_birth': '1984-06-20',
            'spouse_name': 'Meghna',
            'spouse_dob': '1986-11-14',
            'if_any_kids': True,
            'children': [
                {'child_name': 'Arjun', 'child_dob': '2014-03-10', 'Gender': 'Male', 'investments': []},
                {'child_name': 'Priya', 'child_dob': '2017-08-25', 'Gender': 'Female', 'investments': [
                    {'type': 'SUKANYA SAMRIDDHI YOJANA', 'commencement_date': '2018-04-01', 'annual_contribution': 50000, 'current_value': 380000}
                ]}
            ],
            'retirement_age': 60
        },
        'investment_details': {
            'financial_summary': [
                {
                    'monthly_salary': 230000,
                    'monthly_expenses_excl_emis': 85000,
                    'other_income(rental/interest/other)': 8000,
                    'lump_sum_available': 320000,
                    'miscellaneous_kids_education_expenses_monthly': 10000,
                    'annual_vacation_expenses': 60000,
                    'emergency_fund_maintained': 600000
                }
            ],
            'real_estate_investment': [
                {'current_market_value': 7500000, 'rental_income': 0}
            ],
            'retirement_investments': {
                'epf': [
                    {'current_value': 1800000, 'employee_employer_contribution_monthly': 19000, 'interest_rate': 0.085}
                ],
                'ppf': [
                    {'current_value': 320000, 'annual_contribution': 36000, 'interest_rate': 0.075}
                ],
                'nps': []
            },
            'bonds': [],
            'mutual_funds': [
                {'current_value': 1100000, 'expected_annual_return': 0.12, 'sip_amount': 18000}
            ],
            'direct_equity': [{'portfolio_value': 180000}],
            'reits': [{'current_value': 0}],
            'pms_aif': [{'current_value': 0}],
            'esops': [{'vested_esops_value': 0, 'unvested_esops_value': 0}],
            'fixed_deposits': [
                {'name_of_bank': 'hdfc_bank', 'principal_amount': 280000, 'interest_rate': 0.068, 'maturity_date': '09-2029'}
            ],
            'other_investments': []
        },
        'financial_goals': [
            {'goal_name': 'Arjun Marriage', 'capital_required_today': 1500000, 'target_year': 2040},
            {'goal_name': 'Foreign Vacation', 'capital_required_today': 600000, 'target_year': 2029}
        ],
        'liabilities': [
            {
                'type': 'Home loan',
                'outstanding_balance': 7200000,
                'interest_rate': 0.0875,
                'emi_amount': 62000,
                'is_under_penalty_period': False,
                'time_left_to_come_out_of_penalty_period(months)': 0
            },
            {
                'type': 'Renovation loan',
                'outstanding_balance': 1200000,
                'interest_rate': 0.105,
                'emi_amount': 18000,
                'is_under_penalty_period': False,
                'time_left_to_come_out_of_penalty_period(months)': 0
            },
            {
                'type': 'Car loan',
                'outstanding_balance': 650000,
                'interest_rate': 0.092,
                'emi_amount': 14500,
                'is_under_penalty_period': False,
                'time_left_to_come_out_of_penalty_period(months)': 0
            }
        ],
        'education_planning': [
            {
                'name_of_kid': 'Arjun',
                'dob': '2014-03-10',
                'graduation_stream': 'B.Tech',
                'graduation_destination': 'Domestic',
                'fund_allocated_for_graduation': 0,
                'post_graduation_stream': 'MBA',
                'post_graduation_destination': 'Domestic',
                'scheme_for_education': []
            },
            {
                'name_of_kid': 'Priya',
                'dob': '2017-08-25',
                'graduation_stream': 'B.Tech',
                'graduation_destination': 'Domestic',
                'post_graduation_stream': 'NA',
                'post_graduation_destination': 'NA',
                'scheme_for_education': []
            }
        ],
        'life_insurance': []
    }
}

# Change this key to quickly run a different persona.
default_profile = "single_mother_salaried_two_kids"
client_data = client_profiles[default_profile]
