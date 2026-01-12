"""
ELT17 - English Life Table No. 17 (Males)
Source: Office for National Statistics (ONS)
Based on mortality data from 2010-2012

qx = probability of death within one year for a person aged x
"""

# ELT17 Males qx values (probability of death within one year)
# Index = age (0-100)
ELT17_MALES_QX = {
    0: 0.004707,
    1: 0.000337,
    2: 0.000186,
    3: 0.000150,
    4: 0.000121,
    5: 0.000107,
    6: 0.000096,
    7: 0.000088,
    8: 0.000083,
    9: 0.000083,
    10: 0.000089,
    11: 0.000100,
    12: 0.000117,
    13: 0.000140,
    14: 0.000169,
    15: 0.000206,
    16: 0.000260,
    17: 0.000334,
    18: 0.000418,
    19: 0.000495,
    20: 0.000553,
    21: 0.000588,
    22: 0.000604,
    23: 0.000607,
    24: 0.000605,
    25: 0.000601,
    26: 0.000598,
    27: 0.000600,
    28: 0.000607,
    29: 0.000622,
    30: 0.000646,
    31: 0.000680,
    32: 0.000724,
    33: 0.000780,
    34: 0.000848,
    35: 0.000928,
    36: 0.001021,
    37: 0.001128,
    38: 0.001249,
    39: 0.001386,
    40: 0.001538,
    41: 0.001707,
    42: 0.001893,
    43: 0.002099,
    44: 0.002326,
    45: 0.002575,
    46: 0.002849,
    47: 0.003149,
    48: 0.003479,
    49: 0.003842,
    50: 0.004242,
    51: 0.004683,
    52: 0.005171,
    53: 0.005712,
    54: 0.006315,
    55: 0.006988,
    56: 0.007742,
    57: 0.008589,
    58: 0.009541,
    59: 0.010615,
    60: 0.011826,
    61: 0.013195,
    62: 0.014743,
    63: 0.016496,
    64: 0.018485,
    65: 0.020745,
    66: 0.023318,
    67: 0.026251,
    68: 0.029601,
    69: 0.033429,
    70: 0.037809,
    71: 0.042827,
    72: 0.048582,
    73: 0.055188,
    74: 0.062773,
    75: 0.071487,
    76: 0.081499,
    77: 0.093002,
    78: 0.106217,
    79: 0.121392,
    80: 0.138802,
    81: 0.158745,
    82: 0.181534,
    83: 0.207489,
    84: 0.236922,
    85: 0.270111,
    86: 0.307256,
    87: 0.348429,
    88: 0.393512,
    89: 0.442143,
    90: 0.493651,
    91: 0.547108,
    92: 0.601335,
    93: 0.654943,
    94: 0.706489,
    95: 0.754621,
    96: 0.798189,
    97: 0.836310,
    98: 0.868438,
    99: 0.894366,
    100: 1.000000,  # Assume 100% mortality at 100+
}


def get_qx(age: int, table: str = "ELT17_MALES") -> float:
    """
    Get the annual probability of death (qx) for a given age.

    Args:
        age: The age in complete years
        table: The mortality table to use (default: ELT17_MALES)

    Returns:
        The probability of death within one year
    """
    if table != "ELT17_MALES":
        raise ValueError(f"Unknown mortality table: {table}")

    # Cap at age 100
    age = min(age, 100)
    age = max(age, 0)

    return ELT17_MALES_QX[age]


def annual_to_monthly_qx(qx_annual: float) -> float:
    """
    Convert an annual mortality rate to a monthly rate.

    Uses the formula: qx_monthly = 1 - (1 - qx_annual)^(1/12)
    This assumes uniform distribution of deaths over the year.

    Args:
        qx_annual: Annual probability of death

    Returns:
        Monthly probability of death
    """
    return 1 - (1 - qx_annual) ** (1/12)
