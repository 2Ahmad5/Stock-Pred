# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from datetime import datetime
import calendar

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import Blueprint

regres = Blueprint('regres', __name__)

# app = Flask(__name__)
# CORS(app)

# %%
# Writing backtesting_aux

def backtesting_aux(start_date, end_date, tickers, allocation, rebalancing, data_short, ff5, start_balance):

    # Start prepping for backtesting
    t = data_short.pivot(index='date', columns='ticker_new', values='ret')
    t_dates = t.index  
    t_returns = t[tickers] 

    n_months = len(t_dates)
    n_assets = len(tickers)

    y_aux = np.floor(t_dates / 100).astype(int)  # extract year
    m_aux = (t_dates % 100).astype(int)  # extract month
    d_aux = [calendar.monthrange(y, m)[1] for y, m in zip(y_aux, m_aux)]  # get end of month day
    dates_aux = pd.to_datetime(dict(year=y_aux, month=m_aux, day=d_aux))

    if not n_months == len(ff5):
        print('Error: Number of months for tickers different than rf number of months')
        return

    dollar_amt = np.zeros((n_months, n_assets))
    
    allocation = np.array(allocation, dtype=float)  # Ensure allocation is a numpy array
    
    if rebalancing == 'monthly':
        for t in range(n_months):
            if t == 0:
                dollar_amt[t, :] = start_balance * np.nan_to_num(allocation / 100) * (1 + t_returns.iloc[t].values)
            else:
                dollar_amt[t, :] = np.sum(dollar_amt[t - 1, :]) * np.nan_to_num(allocation / 100)
                dollar_amt[t, :] *= (1 + t_returns.iloc[t].values)

    elif rebalancing == 'None':
        dollar_amt_start = start_balance * np.nan_to_num(allocation / 100)
        cum_returns = (1 + t_returns).cumprod()
        dollar_amt = np.tile(dollar_amt_start, (n_months, 1)) * cum_returns.values

    elif rebalancing == 'yearly':
        for t in range(n_months):
            if t == 0:
                dollar_amt[t, :] = start_balance * np.nan_to_num(allocation / 100) * (1 + t_returns.iloc[t].values)
            elif t % 12 != 0:  # Rebalance yearly 
                dollar_amt[t, :] = dollar_amt[t - 1, :] * (1 + t_returns.iloc[t].values)
            else:
                dollar_amt[t, :] = np.sum(dollar_amt[t - 1, :]) * np.nan_to_num(allocation / 100)
                dollar_amt[t, :] *= (1 + t_returns.iloc[t].values)

    # Portfolio value
    pv = np.sum(dollar_amt, axis=1)
    pv2 = np.concatenate(([start_balance], pv))

    # Annual returns
    ann_return_cagr = (pv2[-1] / start_balance) ** (12 / n_months) - 1
    ann_return_average = np.nanmean(np.diff(pv2) / pv2[:-1]) * 12
    ann_std = np.nanstd(np.diff(pv2) / pv2[:-1]) * np.sqrt(12)
    sharpe_ratio = (ann_return_average - np.nanmean(ff5['RF'])*12) / ann_std
    p_returns = np.diff(pv2) / pv2[:-1]

    num = p_returns - ff5['RF'].values
    den = np.where(num > 0, 0, num)
    sortino_ratio = np.nanmean(num) * 12 / (np.sqrt(12) * np.nanstd(den))

    # Annual returns by year
    unique_years = np.unique(y_aux)
    ann_ret = []
    for y in unique_years:
        returns_aux = p_returns
        indicator = y_aux == y
        returns_y = returns_aux[indicator]
        aux_ret = np.cumprod(returns_y + 1)

        ann_ret.append([y, aux_ret[-1] - 1, len(returns_y), np.min(m_aux[indicator]), np.max(m_aux[indicator])])

    # Compute drawdowns
    cumulative_max = np.maximum.accumulate(pv)
    drawdowns = (pv - cumulative_max) / cumulative_max

    # Group drawdowns
    drawdown_group = np.full_like(drawdowns, np.nan)
    non_zero_mask = drawdowns != 0
    start_of_group = np.concatenate(([False], np.diff(non_zero_mask.astype(int)) > 0))
    group_ids = np.cumsum(start_of_group)
    drawdown_group[non_zero_mask] = group_ids[non_zero_mask]

    # Get worst 3 drawdowns
    min_values = pd.Series(drawdowns[non_zero_mask]).groupby(drawdown_group[non_zero_mask]).min()
    min_values_result = min_values.sort_values().head(3)

    # Prepare drawdown table
    drawdowns_tab = []
    for j, (group_id, min_val) in enumerate(min_values_result.items()):
        indicator = drawdown_group == group_id
        drawdowns_short = drawdowns[indicator]
        dates_short = dates_aux[indicator]
        start_date = dates_short.min()
        end_date = dates_short.iloc[np.argmin(drawdowns_short)]
        no_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        recovery_date = dates_short.max()
        recovery_time = (recovery_date.year - end_date.year) * 12 + (recovery_date.month - end_date.month)
        underwater_period = (recovery_date.year - start_date.year) * 12 + (recovery_date.month - start_date.month)

        drawdowns_tab.append([j + 1, start_date, end_date, no_months, recovery_date, recovery_time, underwater_period, min_val])

    # Format drawdowns table into a DataFrame
    drawdowns_tab2 = pd.DataFrame(drawdowns_tab, columns=[
        'Rank', 'Start date', 'End date', 'Length', 'Recovered by', 'Recovery time', 'Underwater period', 'Drawdown'
    ])
    drawdowns_tab2['Start date'] = drawdowns_tab2['Start date'].dt.strftime('%b-%Y')
    drawdowns_tab2['End date'] = drawdowns_tab2['End date'].dt.strftime('%b-%Y')
    drawdowns_tab2['Recovered by'] = drawdowns_tab2['Recovered by'].dt.strftime('%b-%Y')

    return allocation, tickers, dates_aux, drawdowns, ann_ret, sortino_ratio, sharpe_ratio, pv, ann_return_cagr, ann_return_average, ann_std, p_returns, drawdowns_tab2

def backtesting(start_date, end_date, tickers, allocation1, allocation2, allocation3, rebalancing, benchmark, start_balance):

    #edited
    portfolio_growths = {}
    annual_returns_data = {
        "labels": [],
        "datasets": []
    }
    drawdown_data = {
        "dates": None,
        "portfolios": {} 
    }
    port_allocations = {}
    drawdown_print = {}
    regression_analysis = {}
    constraint = ""
    error = ""



    # Ensure allocations are properly handled as numeric arrays
    allocation1 = np.array(allocation1, dtype=float)
    allocation2 = np.array(allocation2, dtype=float)
    allocation3 = np.array(allocation3, dtype=float)

    # Ensure NaN handling in allocations
    allocation1 = np.where(allocation1 == None, np.nan, allocation1)
    allocation2 = np.where(allocation2 == None, np.nan, allocation2)
    allocation3 = np.where(allocation3 == None, np.nan, allocation3)
    
    # Load Data
    return_data = pd.read_csv("ETF_returns_v3.csv")
    return_data['date'] = return_data['year'] * 100 + return_data['month']
    return_data = return_data.drop(columns=['month', 'year'])

    final_data = return_data.sort_values(by=['ticker_new', 'date'])

    # Cross-check allocations
    ind_alloc = [0, 0, 0, 0]  # This vector stores which of the 3 allocations and benchmark should be used
    portfolio_name = ['Portfolio 1', 'Portfolio 2', 'Portfolio 3', 'Benchmark']

    if not np.isnan(allocation1).all():
        ind_alloc[0] = 1
    if not np.isnan(allocation2).all():
        ind_alloc[1] = 1
    if not np.isnan(allocation3).all():
        ind_alloc[2] = 1
    if benchmark != 'None':
        ind_alloc[3] = 1

    # Some cross-checks
    for p in range(3):
        if ind_alloc[p] == 1:
            if p == 0:
                alloc = allocation1
            elif p == 1:
                alloc = allocation2
            elif p == 2:
                alloc = allocation3

            # Check that each positive weight has a ticker
            indicator = alloc > 0
            n_alloc = sum(indicator)
            tickers_aux = [tickers[i] for i, x in enumerate(indicator) if x]
            n_tickers = sum([1 for t in tickers_aux if t])

            if n_tickers != n_alloc:
                print(f"Error: The number of weights needs to be the same as the number of tickers in {portfolio_name[p]}")
                error = f"Error: The number of weights needs to be the same as the number of tickers in {portfolio_name[p]}"

                return portfolio_growths, annual_returns_data, drawdown_data, port_allocations, drawdown_print, regression_analysis, constraint, error

            # Check that every element of allocation is between zero and 100
            indicator = (alloc >= 0) & (alloc <= 100)
            if n_alloc != sum(indicator):
                print(f"Error: Weights need to be between zero and 100 in {portfolio_name[p]}")
                error = f"Error: Weights need to be between zero and 100 in {portfolio_name[p]}"
                return portfolio_growths, annual_returns_data, drawdown_data, port_allocations, drawdown_print, regression_analysis, constraint, error

            # Check allocation adds up to 100
            if not np.nansum(alloc) == 100:
                print(f"Error: Weights need to add up to 100 in {portfolio_name[p]}")
                error = f"Error: Weights need to add up to 100 in {portfolio_name[p]}"
                return portfolio_growths, annual_returns_data, drawdown_data, port_allocations, drawdown_print, regression_analysis, constraint, error

    # Filter data for the tickers in the allocation
    data_short = final_data[final_data['ticker_new'].isin(tickers)]

    # Remove NaNs in returns
    data_short = data_short.dropna(subset=['ret'])

    # Get the minimum and maximum date for each ticker
    non_empty_idx = [t for t in tickers if t]
    min_date = data_short.groupby('ticker_new')['date'].min()
    max_date = data_short.groupby('ticker_new')['date'].max()

    max_min_date = min_date.max()
    min_max_date = max_date.min()

    if not start_date:
        start_date = max_min_date

    if max_min_date > start_date:
        print(f"Data range will start from {max_min_date} because that is the first available date for ticker {non_empty_idx[min_date.argmax()]}")
        constraint = f"Data range will start from {max_min_date} because that is the first available date for ticker {non_empty_idx[min_date.argmax()]}"
        start_date = max_min_date

    if not end_date:
        end_date = min_max_date

    if start_date >= end_date:
        print("Error: Start date cannot be after end date")
        error = "Error: Start date cannot be after end date"
        return

    # Filter data based on date range
    data_short = data_short[(data_short['date'] >= start_date) & (data_short['date'] <= end_date)]

    # Get risk-free rate data (Fama-French factors)
    ff5 = pd.read_csv('F-F_Research_Data_5_Factors_2x3.csv', sep=',', skiprows=1)
    ff5.columns = ['date', 'Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'RF']
    ff5 = ff5[(ff5['date'] >= start_date) & (ff5['date'] <= end_date)]

    # Append benchmark returns to the dataset
    ff5['ret'] = ff5['Mkt-RF'] + ff5['RF']
    benchmark_data = pd.DataFrame({
        'date': ff5['date'],
        'ret': ff5['ret']/100,
        'ticker_new': 'CRSPVW'
    })
    data_short = pd.concat([data_short, benchmark_data])

    # Keep only risk-free rate for sharpe ratio calculation
    ff5 = ff5[['date', 'RF']]
    ff5['RF'] = ff5['RF']/100
    
    # Process each portfolio allocation
    output = {}
    for p in range(3):
        if ind_alloc[p] == 1:
            if p == 0:
                alloc = allocation1
                tickers2 = [t for i, t in enumerate(tickers) if not np.isnan(alloc[i])]
            elif p == 1:
                alloc = allocation2
                tickers2 = [t for i, t in enumerate(tickers) if not np.isnan(alloc[i])]
            elif p == 2:
                alloc = allocation3
                tickers2 = [t for i, t in enumerate(tickers) if not np.isnan(alloc[i])]

            alloc = [a for a in alloc if not np.isnan(a)]

            results = backtesting_aux(start_date, end_date, tickers2, alloc, rebalancing, data_short, ff5, start_balance)
            output[p] = {key: value for key, value in zip(['allocation', 'tickers', 'dates_aux', 'drawdowns', 'ann_ret', 'sortino_ratio', 'sharpe_ratio', 'pv', 'ann_return_cagr', 'ann_return_average', 'ann_std', 'p_returns', 'drawdowns_tab2'], results)}

    # Benchmark
    p = 3
    alloc = np.array([100])
    tickers2 = np.array(['CRSPVW']) if benchmark == 'None' else np.array(benchmark)
    results = backtesting_aux(start_date, end_date, tickers2, alloc, rebalancing, data_short, ff5, start_balance)
    output[p] = {key: value for key, value in zip(['allocation', 'tickers', 'dates_aux', 'drawdowns', 'ann_ret', 'sortino_ratio', 'sharpe_ratio', 'pv', 'ann_return_cagr', 'ann_return_average', 'ann_std', 'p_returns', 'drawdowns_tab2'], results)}

    # Output results and generate plots
    print(f'Portfolio Backtesting {start_date} - {end_date}')






    # edited
    for p in range(3):
        if ind_alloc[p] == 1:
            print(f"{portfolio_name[p]} allocation:")
            print(pd.DataFrame(output[p]['allocation'], index=output[p]['tickers'], columns=["Allocation"]))


            # edited
            port_allocations[portfolio_name[p]] = {}
            for t in range(len(output[p]['tickers'])):
                port_allocations[portfolio_name[p]][output[p]['tickers'][t]] = float(output[p]['allocation'][t]) 

    



    # Performance summary
    ps_table = pd.DataFrame(index=[
        'Start Balance', 'End Balance', 'Annualized Return (CAGR)', 'Annualized Standard Deviation', 
        'Best Year', 'Worst Year', 'Maximum drawdown', 'Sharpe Ratio', 'Sortino Ratio', 'Correlation with Benchmark'
    ])
    
    for p in range(4):
        if ind_alloc[p] == 1:
            col_data = [
                start_balance,
                output[p]['pv'][-1],
                output[p]['ann_return_cagr'],
                output[p]['ann_std'],
                max([row[1] for row in output[p]['ann_ret']]),
                min([row[1] for row in output[p]['ann_ret']]),
                min(output[p]['drawdowns']),
                output[p]['sharpe_ratio'],
                output[p]['sortino_ratio'],
                np.corrcoef(output[p]['p_returns'], output[3]['p_returns'])[0, 1]
            ]
            ps_table[portfolio_name[p]] = col_data
    
    print("Performance Summary")

    # print(ps_table)

    # Portfolio Growth Plot
    # plt.figure(figsize=(12, 4))
    # for p in range(4):
    #     if ind_alloc[p] == 1:
    #         plt.plot(output[p]['dates_aux'], output[p]['pv'], label=portfolio_name[p], linewidth=2.5)
    # plt.legend(loc='upper left')
    # plt.title('Portfolio Growth')
    # plt.show()




    # edited Portfolio Growth Plot
    
    plt.figure(figsize=(12, 4))
    for p in range(4):
        if ind_alloc[p] == 1:

            x_values = pd.to_datetime(output[p]['dates_aux']).dt.strftime('%Y-%m-%d').tolist()
            y_values = output[p]['pv'].tolist()
            
            # Add to the dictionary with portfolio name as the key
            portfolio_growths[portfolio_name[p]] = [x_values, y_values]

            plt.plot(output[p]['dates_aux'], output[p]['pv'], label=portfolio_name[p], linewidth=2.5)
    plt.legend(loc='upper left')
    plt.title('Portfolio Growth')
    # plt.show()

    # print(portfolio_growths)



    # Annual Returns Plot
    
    # x values represent the years on the benchmark portfolio
    
    # t = next((i for i, x in enumerate(ind_alloc) if x), None)
    # x = [row[0] for row in output[t]['ann_ret']]  

    # # Filter y_values based on ind_alloc[p] == 1 and only process portfolios that are active
    # y_values = np.column_stack([
    #     [row[1] for row in output[p]['ann_ret']] if ind_alloc[p] == 1 and output[p]['ann_ret'] else [np.nan] * len(x)
    #     for p in range(4) if ind_alloc[p] == 1
    # ])

    # # Create a list of portfolio labels for the active portfolios
    # active_portfolio_names = [portfolio_name[p] for p in range(4) if ind_alloc[p] == 1]

    # # Plotting the annual returns for each active portfolio
    # width = 0.2  # Width of each bar
    # n_portfolios = y_values.shape[1]  # Number of active portfolios

    # plt.figure(figsize=(12, 6))

    # # Loop through active portfolios and plot with an offset
    # for i in range(n_portfolios):
    #     plt.bar(np.array(x) + i * width, y_values[:, i] * 100, width, label=active_portfolio_names[i])
    
    # plt.xticks(x)
    # plt.xlabel('Year')
    # plt.ylabel('Annual Returns (%)')
    # plt.legend(loc='best')
    # plt.title('Annual Returns by Portfolio')
    # plt.show()


    # edited




    t = next((i for i, x in enumerate(ind_alloc) if x), None)
    x = [int(row[0]) for row in output[t]['ann_ret']]  

    annual_returns_data["labels"] = x

    # Filter y_values based on ind_alloc[p] == 1 and only process portfolios that are active
    y_values = np.column_stack([
        [float(row[1]) if row[1] is not None else np.nan for row in output[p]['ann_ret']] 
        if ind_alloc[p] == 1 and output[p]['ann_ret'] else [np.nan] * len(x)
        for p in range(4) if ind_alloc[p] == 1
    ])

    # Create a list of portfolio labels for the active portfolios
    active_portfolio_names = [portfolio_name[p] for p in range(4) if ind_alloc[p] == 1]

    # print(active_portfolio_names, "kjvndkfnvdk")
    for i, portfolio in enumerate(active_portfolio_names):
        dataset = {
            "label": portfolio,  # Portfolio name
            "data": [round(float(value) * 100, 2) if not np.isnan(value) else None for value in y_values[:, i]],
            "backgroundColor": f"rgba({100 + i * 30}, {150 - i * 20}, {200 + i * 20}, 0.6)",
            "borderColor": f"rgba({100 + i * 30}, {150 - i * 20}, {200 + i * 20}, 1)",
            "borderWidth": 1
        }
        annual_returns_data["datasets"].append(dataset)

    # print(annual_returns_data)



    # Plotting the annual returns for each active portfolio
    width = 0.2  # Width of each bar
    n_portfolios = y_values.shape[1]  # Number of active portfolios

    plt.figure(figsize=(12, 6))

    # Loop through active portfolios and plot with an offset
    for i in range(n_portfolios):
        plt.bar(np.array(x) + i * width, y_values[:, i] * 100, width, label=active_portfolio_names[i])
    
    plt.xticks(x)
    plt.xlabel('Year')
    plt.ylabel('Annual Returns (%)')
    plt.legend(loc='best')
    plt.title('Annual Returns by Portfolio')
    # plt.show()





    # Drawdown Plot
    plt.figure(figsize=(12, 4))
    print(portfolio_name, "lfmvkdfn ")
    for p in range(4):
        if ind_alloc[p] == 1:
            plt.plot(output[p]['dates_aux'], output[p]['drawdowns'] * 100, label=portfolio_name[p], linewidth=1.5)
    plt.title('Drawdowns')
    plt.legend()
    # plt.show()




    # edited
    
    plt.figure(figsize=(12, 4))
    for p in range(4):
        if ind_alloc[p] == 1:
            dates = pd.to_datetime(output[p]['dates_aux']).dt.strftime('%Y-%m-%d').tolist()
            drawdowns = output[p]['drawdowns'] * 100 

            if drawdown_data["dates"] is None:
                drawdown_data["dates"] = dates

            drawdown_data["portfolios"][portfolio_name[p]] = [round(float(value), 2) for value in drawdowns]
            plt.plot(output[p]['dates_aux'], output[p]['drawdowns'] * 100, label=portfolio_name[p], linewidth=1.5)

    # plt.title('Drawdowns')
    # plt.legend()
    # plt.show()

    # print(drawdown_data)




    # Get top 3 drawdowns for each portfolio
    for p in range(3):
        if ind_alloc[p] == 1:
            print(f"Top 3 drawdowns {portfolio_name[p]}")
            portfolio_key = portfolio_name[p]
            drawdown_df = output[p]['drawdowns_tab2']
            print(output[p]['drawdowns_tab2']) 


            # edited
            drawdown_print[portfolio_key] = {col: drawdown_df[col].tolist() for col in drawdown_df.columns}

    


    # Regression analysis
    for p in range(3):
        if ind_alloc[p] == 1:
            print(f"Regression analysis {portfolio_name[p]}")



            # Independent and dependent variables
            x_var = output[p]['p_returns'] - ff5['RF']  # Portfolio returns minus risk-free rate
            y_var = output[3]['p_returns'] - ff5['RF']  # Benchmark returns minus risk-free rate

            # Add a constant to x_var for the intercept in the regression model
            x_var_with_constant = sm.add_constant(x_var)

            # Fit the linear model
            model = sm.OLS(y_var, x_var_with_constant).fit()

            # Print R-squared and Adjusted R-squared
            print(f"R square {model.rsquared:.2f}")
            print(f"Adjusted R square {model.rsquared_adj:.2f}")
            print(f"Observations {int(model.nobs)}")


            # Combine the regression results into a DataFrame for easy display
            aux = pd.DataFrame({
                'Loadings': model.params,
                'Standard Errors': model.bse,
                't-stat': model.tvalues,
                'p-value': model.pvalues
            })
            aux.index = ['alpha', 'beta']
            print(aux)


            # Calculate and print annualized alpha
            annualized_alpha = model.params['const'] * 12 
            print(f'Annualized alpha {annualized_alpha:.4f}')




            # edited
            temp = aux.to_dict(orient='index')
            temp['R-squared'] = round(float(model.rsquared), 2)
            temp['Adjusted R-squared'] = round(float(model.rsquared_adj), 2)
            temp['Observations'] = int(model.nobs)
            temp['Annualized alpha'] = float(annualized_alpha)


            regression_analysis[portfolio_name[p]] = temp




    # edited        
    # print(portfolio_growths)
    # print("dffffffffffffffffffffffffffffffffffffffffffff")
    # print(annual_returns_data)
    # print(port_allocations)
    # print(drawdown_print)
    # print(regression_analysis)
    return portfolio_growths, annual_returns_data, drawdown_data, port_allocations, drawdown_print, regression_analysis, constraint, error
    


# %%
# Inputs test 1
# start_date = 197001
# end_date = None  
# tickers = ['VTI', 'VNQ', 'VXUS', 'BND', 'MUB', '', '', '', '', 'SPLG'] 

# allocation1 = [48, 8, 24, 20, None, None, None, None, None, None]  
# allocation2 = [48, None, 14, None, 30, None, None, None, None, 8]
# allocation3 = [None] 

# rebalancing = 'monthly'  
# benchmark = ['CRSPVW']  
# start_balance = 10000 


# %%
# Input test 2
# start_date = 197001
# end_date = None  
# tickers = ['VTI', 'VNQ', '', 'BND', 'MUB', '', '', '', '', 'SPLG'] 

# allocation1 = [48, 8, None, 20, 24, None, None, None, None, None]  
# allocation2 = [48, None, None, None, 30, None, None, None, None, 22]
# allocation3 = [None, None, None, None, 50, None, None, None, None, 50] 

# rebalancing = 'monthly'  
# benchmark = ['CRSPVW']  
# start_balance = 10000 

# %%
# Input test 3
start_date = 197501
end_date = None  
tickers = ['VTI', '', '', 'BND', 'MUB', '', '', '', '', 'SPLG'] 

allocation1 = [None, None, None, None, None, None, None, None, None, None]  
allocation2 = [48, None, None, None, 30, None, None, None, None, 22]
allocation3 = [None, None, None, None, 50, None, None, None, None, 50] 

rebalancing = 'monthly'  
benchmark = ['CRSPVW']  
start_balance = 10000 

# %%
# backtesting(start_date, end_date, tickers, allocation1, allocation2, allocation3, rebalancing, benchmark, start_balance)

# %%
@regres.route('/regres', methods=['POST'])
def process3():

    data = request.json
    ticker_list = data.get('ticker_list', [])
    start_date = data.get('start', None)
    end_date = data.get('end', None)
    benchmark = data.get('benchmark', [])
    allocation1 = data.get('allocation1', [])
    allocation2 = data.get('allocation2', [])
    allocation3 = data.get('allocation3', [])
    start_balance = data.get('startBalance', 0)
    rebalancing = data.get('rebalance', 'monthly')

    print(ticker_list, start_date, end_date, benchmark, allocation1, allocation2, allocation3, start_balance, rebalancing)

    portfolio_growths, annual_returns_data, drawdown_data, port_allocations, drawdown_print, regression_analysis, constraint, error = backtesting(start_date, end_date, tickers, allocation1, allocation2, allocation3, rebalancing, benchmark, start_balance)
    # print(portfolio_growths, annual_returns_data, drawdown_data)
    response_data = {
        'portfolio_growths': portfolio_growths,
        'annual_returns_data': annual_returns_data,
        'drawdown_data': drawdown_data,
        'port_allocations': port_allocations,
        'drawdown_print': drawdown_print,
        'regression_analysis': regression_analysis,
        'constraint': constraint,
        'error': error,
    }


    return jsonify(response_data)

