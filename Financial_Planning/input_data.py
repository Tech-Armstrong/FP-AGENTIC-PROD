"""
Client Financial Data - Sample Input

What this file does:
This script contains sample client financial data used for testing and demonstration.
It provides a comprehensive data structure covering all aspects of personal finance.

What this file contains:
- client_data: Dictionary containing complete client financial profile including:
  - client_data: Personal details (name, DOB, spouse, children, retirement age)
  - investment_details: Assets portfolio (real estate, retirement schemes, MFs, stocks, etc.)
  - financial_goals: Life goals with capital requirements and target years
  - liabilities: Loans with outstanding balance, EMI, and interest rates
  - education_planning: Children's education goals with streams and destinations
  - life_insurance: Insurance policies with premiums and maturity details
"""
"""
client_data={
  'client_data': {
    'name': 'Rohit',
    'pan': '',
    'organization_name': 'ABC Pvt Ltd',
    'date_of_birth': '1991-09-14',
    'spouse_name': 'Neha',
    'spouse_dob': '1996-09-21',
    'if_any_kids': True,
    'children': [
      {'child_name': 'Jaidev', 'child_dob': '2011-08-26'},
      {'child_name': 'Nivedya', 'child_dob': '2017-04-16'}
    ],
    'retirement_age': 52
  },

  'investment_details': {
    'financial_summary': [
      {
        'monthly_salary': 100000,
        'monthly_expenses_excl_emis': 55000,
        'other_income(rental/interest/other)': 0,
        'lump_sum_available': 200000,
        'miscellaneous_kids_education_expenses_monthly': 0,
        'annual_vacation_expenses': 0,
        'emergency_fund_maintained': 500000
      }
    ],

    'real_estate_investment': [
      {
        'current_market_value': 18000000,
        'rental_income': 0
      }
    ],

    'retirement_investments': {
      'epf': [
        {
          'current_value': 30000,
          'employee_employer_contribution_monthly': 15000,
          'interest_rate': 0.085
        }
      ],
      'ppf': [
        {
          'current_value': 0,
          'annual_contribution': 0,
          'interest_rate': 0.075
        }
      ],
      'nps': []
    },

    'bonds': [],

    'mutual_funds': [
      {
        'current_value': 80000,
        'expected_annual_return': 0.12,
        'sip_amount': 0
      }
    ],

    'direct_equity': [
      { 'portfolio_value': 10000 }
    ],

    'reits': [
      { 'current_value': 0 }
    ],

    'pms_aif': [
      { 'current_value': 0 }
    ],

    'esops': [
      {
        'vested_esops_value': 0,
        'unvested_esops_value': 0
      }
    ],

    'fixed_deposits': [
      {
        'name_of_bank': 'state_bank_of_india',
        'principal_amount': 0,
        'interest_rate': 0.065,
        'maturity_date': '07-2035'
      }
    ],

    'other_investments': []
  },

  'financial_goals': [
    {'goal_name': 'Vacation', 'capital_required_today': 250000, 'target_year': 2027}
  ],

  'liabilities': [],

  'education_planning': [
    { 
      'name_of_kid': 'Jaidev',
      'dob': '2023-08-26',
      'graduation_stream': 'B.Tech',
      'graduation_destination': 'Domestic',
      'fund_allocated_for_graduation': 0,
      'post_graduation_stream': 'NA',
      'post_graduation_destination': 'NA',
      'scheme_for_education': []
    },
    { 
      'name_of_kid': 'Nivedya',
      'dob': '2021-04-16',
      'graduation_stream': 'B.Tech',
      'graduation_destination': 'Domestic',
      'fund_allocated_for_graduation': 0,
      'post_graduation_stream': 'NA',
      'post_graduation_destination': 'NA',
      'scheme_for_education': []
    }
  ],

  'life_insurance': []
}
"""
client_data = {
    'client_data': {
        'name': 'Yash Mehta',
        'pan': '',
        'organization_name': 'ABC Pvt Ltd',
        'date_of_birth': '1992-12-17',
        'spouse_name': 'Priya',
        'spouse_dob': '1996-09-21',
        'if_any_kids': True,
        'children': [
            {'child_name': 'Sahil', 'child_dob': '2011-08-26', 'Gender': 'Male', 'investments': []},
            {
                'child_name': 'Vanshika', 
                'child_dob': '2017-04-16', 
                'Gender': 'Female',
                'investments': [
                    {
                        'type': 'SUKANYA SAMRIDDHI YOJANA',
                        'commencement_date': '2021-05-01',
                        'annual_contribution': 50000,
                        'current_value': 250000
                    }
                ]
            }
        ],
        'retirement_age': 56
    },

    'investment_details': {
        'financial_summary': [
            {
                'monthly_salary': 902250,
                'monthly_expenses_excl_emis': 615000,
                'other_income(rental/interest/other)': 0,
                'lump_sum_available': 200000,
                'miscellaneous_kids_education_expenses_monthly': 0,
                'annual_vacation_expenses': 0,
                'emergency_fund_maintained': 500000
            }
        ],

        'real_estate_investment': [
            {
                'current_market_value': 180000,
                'rental_income': 0
            }
        ],

        'retirement_investments': {
            'epf': [
                {
                    'current_value': 800000,
                    'employee_employer_contribution_monthly': 5000,
                    'interest_rate': 0.085
                }
            ],
            'ppf': [
                {
                    'current_value': 400000,
                    'annual_contribution': 0,
                    'interest_rate': 0.075
                }
            ],
            'nps': [],
            'ulip': [
                {
                    'policy_name': 'ULIP Policy - I',
                    'commencement_date': '2024-01-01',
                    'premium': 100000,
                     'ppt': 7,
                    'term': 15,
                    'maturity_value': 1200000,
                    #'current_value': 260000,
                    'maturity_year': 2035
                }
            ]
        },

        'bonds': [],

        'mutual_funds': [
            {
                'current_value': 1500000,
                'expected_annual_return': 0.12,
                'sip_amount': 0
            }
        ],

        'direct_equity': [
            {'portfolio_value': 250000}
        ],

        'reits': [
            {'current_value': 0}
        ],

        'pms_aif': [
            {'current_value': 0}
        ],

        'esops': [
            {
                'vested_esops_value': 120000,
                'unvested_esops_value': 0
            }
        ],

        'fixed_deposits': [
            {
                'name_of_bank': 'state_bank_of_india',
                'principal_amount': 500000,
                'interest_rate': 0.065,
                'maturity_date': '07-2035'
            }
        ],

        'other_investments': []
    },

    'financial_goals': [
        {'goal_name': 'Vacation', 'capital_required_today': 20000, 'target_year': 2027},
        {'goal_name': 'Vanshika Marriage', 'capital_required_today': 400000, 'target_year': 2043}
    ],

    'liabilities': [
        {
            'type': 'Car loan',
            'outstanding_balance': 100000,
            'interest_rate': 0.0885,
            'emi_amount': 15000,
            'is_under_penalty_period': False,
            'time_left_to_come_out_of_penalty_period(months)': 0
        }
    ],

    'education_planning': [
        { 
            'name_of_kid': 'Sahil',
            'dob': '2011-08-26',
            'graduation_stream': 'B.Tech',
            'graduation_destination': 'Domestic',
            'fund_allocated_for_graduation': 0,
            'post_graduation_stream': 'MBA',
            'post_graduation_destination': 'Domestic',
            'scheme_for_education': []
        },
        { 
            'name_of_kid': 'Vanshika',
            'dob': '2017-04-16',
            'graduation_stream': 'B.Tech',
            'graduation_destination': 'Domestic',
            'fund_allocated_for_graduation': 0,
            'post_graduation_stream': 'MBA',
            'post_graduation_destination': 'Domestic',
            'scheme_for_education': []
        }
    ],

    'life_insurance': []
}