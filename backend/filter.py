import pandas as pd

input_file_path = 'ETF_returns_v3.csv'

output_file_path = 'ETF_tickers_only.csv'

df = pd.read_csv(input_file_path)

unique_cd_values = df['ticker_new'].unique()

unique_df = pd.DataFrame(unique_cd_values, columns=['ticker_new'])

unique_df.to_csv(output_file_path, index=False)

