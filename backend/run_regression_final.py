# %% 
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from statsmodels.stats.stattools import durbin_watson, omni_normtest, jarque_bera
from scipy.stats import skew, kurtosis
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


def run_regression(final_data, ticker, start_date, end_date, model, rolling_period):

    line_graph_1 = []
    line_2 = []
    line_3 = []
    line_4 = []
    line_5 = []
    line_6 = []
    summary_data = {}
    return_table = {}
    middle_titles = []
    middle_values = {}

    data_short = final_data[final_data['ticker_new'] == ticker]
    
    if (end_date is None) or (end_date > data_short['date'].max()):
        end_date = data_short['date'].max()
    if (start_date is None) or (start_date < data_short['date'].min()):
        start_date = data_short['date'].min()
    
    data_short = data_short[(data_short['date'] >= start_date) & (data_short['date'] <= end_date)]
    
    y_var = data_short['ret'] - data_short['RF']
    nobs = y_var.shape[0]
    
    if model == 'CAPM':
        x_var = data_short[['Mkt-RF']]
        factor_names = ['Mkt-Rf']
        n_factors = 1
    elif model == 'FF3':
        x_var = data_short[['Mkt-RF', 'HML', 'SMB']]
        factor_names = ['Mkt-Rf', 'HML', 'SMB']
        n_factors = 3
    elif model == 'FF4':
        x_var = data_short[['Mkt-RF', 'HML', 'SMB', 'MOM']]
        factor_names = ['Mkt-Rf', 'HML', 'SMB', 'MOM']
        n_factors = 4
    elif model == 'FF5':
        x_var = data_short[['Mkt-RF', 'HML', 'SMB', 'CMA', 'RMW']]
        factor_names = ['Mkt-Rf', 'HML', 'SMB', 'CMA', 'RMW']
        n_factors = 5
    
    # Add constant term
    x_var = sm.add_constant(x_var)
    
    # Run regression
    mdl = sm.OLS(y_var, x_var, missing = 'drop').fit()
    
    loadings = mdl.params.values
    
    se = mdl.bse.values
    tStat = mdl.tvalues.values
    pvalue = mdl.pvalues.values
    
    print(f'Regression Output: start date {start_date}, end date {end_date}')
    print(f'R square {mdl.rsquared:.2f}')
    print(f'Adjusted R square {mdl.rsquared_adj:.2f}')
    print(f'Observations {nobs}')
             
    print(f'Annualized alpha {loadings[0] * 12:.4f}')
    
    # Regression Table
    print(mdl.summary())


    # edited
    coefficients = mdl.params
    standard_errors = mdl.bse
    t_statistics = mdl.tvalues
    p_values = mdl.pvalues
    confidence_intervals = mdl.conf_int()

    middle_titles = mdl.params.index.tolist()
    middle_values = {
        title: [
            round(mdl.params[title], 3),
            round(mdl.bse[title], 3),
            round(mdl.tvalues[title], 3),
            round(mdl.pvalues[title], 3),
            round(mdl.conf_int().loc[title, 0], 3),
            round(mdl.conf_int().loc[title, 1], 3)
         ] for title in middle_titles
        
    } 


    summary_data = {
    "R-squared": round(mdl.rsquared, 3),
    "Dep. Variable": "y",
    "Model": "OLS",
    "Adj. R-squared": round(mdl.rsquared_adj, 3),
    "F-statistic": round(mdl.fvalue, 3),
    "Method": "Least Squares",
    "Prob (F-statistic)": "{:.3e}".format(mdl.f_pvalue),
    "date": datetime.now().strftime("%a, %d %b %Y"),
    "time": datetime.now().strftime("%H:%M:%S"),
    "Log-Likelihood": round(mdl.llf,2),
    "AIC": round(mdl.aic, 1),
    "BIC": round(mdl.bic, 1),
    "No. Observations": mdl.nobs,
    "Df Residuals": mdl.df_resid,
    "Df Model": mdl.df_model,
    "Covariance Type": mdl.cov_type,
    "Durbin-Watson": round(durbin_watson(mdl.resid), 3),
    "Omnibus": round(omni_normtest(mdl.resid)[0], 3),
    "Prob(Omnibus)": round(omni_normtest(mdl.resid)[1], 3),
    "Jarque-Bera (JB)": round(jarque_bera(mdl.resid)[0], 3),
    "Prob(JB)": round(jarque_bera(mdl.resid)[1], 6),
    "Skew": round(skew(mdl.resid), 3),
    "Kurtosis": round(kurtosis(mdl.resid), 3),
    }



    
    # Create Table with return contribution
    return_contribution = np.full((n_factors + 2, 2), np.nan)
    return_contribution[0, 0] = np.nanmean(y_var) * 12
    return_contribution[1, 0] = loadings[0] * 12
    
    for k in range(n_factors):
        return_contribution[k + 2, 0] = np.nanmean(x_var.iloc[:, k + 1]) * 12
    
    return_contribution[1, 1] = return_contribution[1, 0] / return_contribution[0, 0] * 100
    return_contribution[2:, 1] = loadings[1:] * (np.nanmean(x_var.iloc[:, 1:], axis=0)) * 12 / return_contribution[0, 0] * 100
    
    return_contribution_df = pd.DataFrame(return_contribution, 
                                          columns=['Av. Ann. Excess Return', 'Return Contribution'],
                                          index=[ticker, 'alpha'] + factor_names)
    
    print(return_contribution_df)


    #edited

    def clean_nan_to_none(row):
        return ["None" if np.isnan(x) else round(x, 6) for x in row]


    for label, row in return_contribution_df.iterrows():

        return_table[label] = clean_nan_to_none(row.tolist())


    
    # Rolling regression
    if rolling_period is None or pd.isna(rolling_period):
        rolling_period = 36
    
    if nobs < rolling_period + 10:
        
        print('Not enough observations for rolling regression')
        return line_graph_1, line_2, line_3, line_4, line_5, line_6, summary_data, return_table, middle_titles, middle_values
    else:
        out_roll = np.full((nobs - rolling_period + 1, n_factors + 1), np.nan)
        
        for k in range(rolling_period, nobs + 1):
            start_point = k - rolling_period
            end_point = k
            x_var_roll = x_var.iloc[start_point:end_point, :]
            y_var_roll = y_var.iloc[start_point:end_point]
            mdl_roll = sm.OLS(y_var_roll, x_var_roll, missing = 'drop').fit()
            
            out_roll[k - rolling_period, :] = mdl_roll.params.values
        
        # Make plot of rolling regression
        date_aux = data_short['date'].iloc[rolling_period - 1:].values
        dates_aux = pd.to_datetime(date_aux, format = '%Y%m')
        
        fig, ax1 = plt.subplots(figsize=(14, 7))

        color = 'tab:red'
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Annualized Alpha', color=color)
        ax1.plot(dates_aux, out_roll[:, 0] * 12, color=color)
        ax1.tick_params(axis='y', labelcolor=color)


        # edited
        temp = []
        temp1 = []
        temp2 = []
        temp3 = []
        temp4 = []
        temp5 = []
        for i in range(len(dates_aux)):

            if i < len(dates_aux) and i < len(out_roll) and len(out_roll[i]) > 0:
                temp.append({'x': dates_aux[i].strftime('%Y-%m-%d'), 'y': out_roll[i][0] * 12})

            if i < len(dates_aux) and i < len(out_roll) and len(out_roll[i]) > 1:
                temp1.append({'x': dates_aux[i].strftime('%Y-%m-%d'), 'y': out_roll[i][1]})

            if i < len(dates_aux) and i < len(out_roll) and len(out_roll[i]) > 2:
                temp2.append({'x': dates_aux[i].strftime('%Y-%m-%d'), 'y': out_roll[i][2]})

            if i < len(dates_aux) and i < len(out_roll) and len(out_roll[i]) > 3:
                temp3.append({'x': dates_aux[i].strftime('%Y-%m-%d'), 'y': out_roll[i][3]})

            if i < len(dates_aux) and i < len(out_roll) and len(out_roll[i]) > 4:
                temp4.append({'x': dates_aux[i].strftime('%Y-%m-%d'), 'y': out_roll[i][4]})

            if i < len(dates_aux) and i < len(out_roll) and len(out_roll[i]) > 5:
                temp5.append({'x': dates_aux[i].strftime('%Y-%m-%d'), 'y': out_roll[i][5]})            

        dataset = {
            'label': 'Annualized_Alpha_Data',
            'data': temp,
            'borderWidth': 1,
            'pointRadius': 2,
            'borderColor': 'red'
        }
        dataset1 = {
            'label': 'Mkt-Rf',
            'data': temp1,
            'borderWidth': 1,
            'pointRadius': 2,
            'borderColor': 'orange'
        }
        dataset2 = {
            'label': 'HML' if len(temp2) > 0 else None,
            'data': temp2,
            'borderWidth': 1,
            'pointRadius': 2,
            'borderColor': 'orange'
        }
        dataset3 = {
            'label': 'SMB' if len(temp3) > 0 else None,
            'data': temp3,
            'borderWidth': 1,
            'pointRadius': 2,
            'borderColor': 'orange'
        }
        dataset4 = {
            'label': 'CHA' if len(temp4) > 0 else None,
            'data': temp4,
            'borderWidth': 1,
            'pointRadius': 2,
            'borderColor': 'orange'
        }
        dataset5 = {
            'label': 'RF' if len(temp5) > 0 else None,
            'data': temp5,
            'borderWidth': 1,
            'pointRadius': 2,
            'borderColor': 'orange'
        }


        
        line_graph_1.append(dataset)
        line_2.append(dataset1)
        line_3.append(dataset2)
        line_4.append(dataset3)
        line_5.append(dataset4)
        line_6.append(dataset5)


        linestyles = ['solid', 'dashed', 'dashdot', 'dotted', (0, (3, 1, 1, 1, 1, 1))]

        ax2 = ax1.twinx()  
        color = 'tab:orange'
        ax2.set_ylabel('Factor Loadings', color=color)  
        for k in range(n_factors):
            ax2.plot(dates_aux, out_roll[:, k + 1], label=factor_names[k], linestyle = linestyles[k], color = color)
        ax2.tick_params(axis='y', labelcolor=color)

        fig.tight_layout()  
        fig.legend([f'Alpha'] + factor_names, loc='lower right', ncol=n_factors+1)
        plt.show()

        
        return line_graph_1, line_2, line_3, line_4, line_5, line_6, summary_data, return_table, middle_titles, middle_values

# %% 
# Import data from CSV file
return_data = pd.read_csv("ETF_returns_v3.csv", sep = ',')
return_data['date'] = return_data['year'] * 100 + return_data['month']
return_data.drop(columns=['month', 'year'], inplace=True)

# %% 
# Import factors
mom = pd.read_csv('F-F_Momentum_Factor.csv', sep=',')
mom.columns = ['date', 'MOM']
mom['MOM'] = mom['MOM'].astype('float64')/100

ff5 = pd.read_csv('F-F_Research_Data_5_Factors_2x3.csv', sep=',')
ff5.columns = ['date', 'Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'RF']
for cols in ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'RF']:
    ff5[cols] = ff5[cols].astype('float64')/100

# %% 
# Merge factors
all_factors = pd.merge(mom, ff5, on='date', how='outer').sort_values(by='date')

# %% 
# Merge return data with factors
final_data = pd.merge(return_data, all_factors, on='date', how='outer').sort_values(by=['ticker_new', 'date'])

# %% 
# Set parameters
start_date = 201602
end_date = 202009
rolling_period = 72
ticker = 'AMZN'
model = 'FF5'  # CAPM, FF3, FF4, FF5


# %% 
# Call the run_regression function
# run_regression(final_data, ticker, start_date, end_date, model, rolling_period)

# %%

@app.route('/process2', methods=['POST'])

def process2():
    data = request.json
    ticker = data.get('Tick', '')
    startDate = data.get('Start', 0)
    endDate = data.get('End', 0)
    model = data.get('Mod', '')
    print(ticker, startDate, endDate, model)
    line_graph_1, line2, line3, line4, line5, line6, mdl_summary, tbl_summary, mid_titles, mid_values = run_regression(final_data, ticker, startDate, endDate, model, rolling_period)
    response_data = {
        'line_graph_1': line_graph_1,
        'line2': line2,
        'line3': line3,
        'line4': line4,
        'line5': line5,
        'line6': line6,
        'mdl_summary': mdl_summary,
        'tbl_summary': tbl_summary,
        "mid_titles": mid_titles,
        "mid_values": mid_values
    }
    return jsonify(response_data)


if __name__ == '__main__':
    app.run(port=5001, debug=True)


