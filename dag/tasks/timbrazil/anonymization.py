"""Anonymization functions for TIM-Brazil."""
from pandas import DataFrame


def get_csv_kwargs(compression: str = None) -> dict:
    """Get common csv kwargs for files from TIM.

    Notes:
        We can't use the `skipfooter` argument with dataframe iteration so
        instead we ignore bad lines like the footer and then remove it in
        the `dataframe_transformer_factory`

    Args:
        compression (str, optional): The type of compression for the file.
            Commonly it is 'gzip'.  Defaults to None.

    Returns:
        dict: Arguments that should be passed to PIIOperator
    """
    return dict(
        compression=compression,
        delimiter='|',
        header=None,
        skiprows=1,
        error_bad_lines=False,
        warn_bad_lines=True,
    )


def transform_dataframe(df: DataFrame, msisdn_column: str) -> DataFrame:
    """Transform the dataframe created from TIM file.

    This function should be applied to all raw carrier files from TIM.

    This does the following:
        - Drops the footer
        - Aligns column numbers with TIM format
        - Prepends msisdn column with country code if necessary
    """
    # drop the footer (but just for the last frame in the sequence)
    if df.iloc[-1, 0] == '03':
        df = df.iloc[0:-1, :].copy()

    # increase column numbers by 1 to align with how tim describes data
    df.columns += 1
    # if not numeric then dont prepend country code
    numeric_msisdns = df[msisdn_column].str.isnumeric()
    msisdns = df.loc[numeric_msisdns, msisdn_column].copy()
    # prepend country code where necessary
    df.loc[msisdns.index, msisdn_column] = msisdns.map(_prepend_country_code)
    return df


def _prepend_country_code(value: str) -> str:
    if len(value) == 11:
        return '55' + value
    return value
