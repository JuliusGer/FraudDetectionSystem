fraud_data_sql = '''
    SELECT transaction_id, client_id, model_fraud_marker, operator_fraud_marker, 
    model_decision_timestamp, operator_decision_timestamp
    FROM transactions.fraud_transactions
    WHERE 
    model_fraud_marker is true
    and operator_fraud_marker is null
'''

fraud_stats_sql = ''' 
    SELECT model_decision_timestamp::date as date,
    count(case when model_fraud_marker = True then model_fraud_marker end) as model_fraud_count,
    count(case when operator_fraud_marker = True then operator_fraud_marker end) as operator_fraud_count
    FROM transactions.fraud_transactions 
    WHERE model_decision_timestamp between now()::date-interval '7' day and now()::date
    GROUP BY model_decision_timestamp::date
    ORDER BY model_decision_timestamp::date
'''

operator_actions_sql = '''
    SELECT * 
    FROM operators.operator_stats 
    WHERE date = now()::date
'''

update_transactions_fraud_transactions_sql = '''
    UPDATE transactions.fraud_transactions
    SET operator_fraud_marker = :op_val,
        operator_decision_timestamp = now(),
        operator_id = :op_id
    WHERE transaction_id = :tx_id
'''