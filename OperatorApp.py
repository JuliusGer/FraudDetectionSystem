import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from sqlalchemy import create_engine, text

# --- Параметры подключения к БД ---
db_user = "postgres"
db_password = "admin"
db_host = "localhost"
db_port = "5432"
db_name = "FraudDetection"

engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

# --- Загрузка данных из БД ---
fraud_data = pd.read_sql("""
    SELECT transaction_id, client_id, model_fraud_marker, operator_fraud_marker, 
    model_decision_timestamp, operator_decision_timestamp
    FROM transactions.fraud_transactions
    WHERE 
    model_fraud_marker is true
    and operator_fraud_marker is null
""", engine)

fraud_stats = pd.read_sql("""
    SELECT model_decision_timestamp::date as date,
    count(case when model_fraud_marker = True then model_fraud_marker end) as model_fraud_count,
    count(case when operator_fraud_marker = True then operator_fraud_marker end) as operator_fraud_count
    FROM transactions.fraud_transactions 
    WHERE model_decision_timestamp between now()::date-interval '7' day and now()::date
    GROUP BY model_decision_timestamp::date
    ORDER BY model_decision_timestamp::date
""", engine)

fraud_stats = fraud_stats.melt(id_vars='date', value_vars=['model_fraud_count', 'operator_fraud_count'],
                               var_name='decision_maker', value_name='fraud_count')

operator_actions = pd.read_sql("""
    SELECT * 
    FROM operators.operator_stats 
    WHERE date = now()::date
""", engine)

# --- UI ---
operator_name = "Тестова Т. Т."
operator_id = 1
st.set_page_config(page_title="Фрод-мониторинг", layout="wide")
st.title("Система мониторинга мошенничества")
st.markdown(f"### Оператор: {operator_name}")

# --- Основная таблица ---
st.subheader("Аналитическая таблица фродовых операций")
selected_transaction_id = st.selectbox("Выберите транзакцию для детализации:", options=[""] + fraud_data["transaction_id"].astype(str).tolist())

fraud_data["operator_fraud_marker"] = fraud_data["operator_fraud_marker"].astype(bool)
updated_data = st.data_editor(
    fraud_data[["transaction_id", "client_id", "model_fraud_marker", "operator_fraud_marker"]],
    use_container_width=True,
    num_rows="dynamic",
    key="fraud_editor"
)

# --- Кнопка сохранения ---
if st.button("Отправить результаты"):
    edited_df = updated_data.copy()
    for index, row in edited_df.iterrows():
        operator_value = row["operator_fraud_marker"]
        transaction_id = row["transaction_id"]
        with engine.begin() as conn:
            conn.execute(
                text("""
                        UPDATE transactions.fraud_transactions
                        SET operator_fraud_marker = :op_val,
                            operator_decision_timestamp = now(),
                            operator_id = :op_id
                        WHERE transaction_id = :tx_id
                """),
                {"op_val": operator_value, "op_id": 1, "tx_id": transaction_id}
            )
    st.success("Результаты успешно сохранены.")
    st.rerun()

# --- Графики ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Динамика фродовых операций (по дням)")
    fig1 = px.bar(fraud_stats, x="date", y="fraud_count", color='decision_maker', labels={"date": "Дата", "fraud_count": "Количество"})
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Статистика действий оператора")
    if not operator_actions.empty:
        row = operator_actions.iloc[0]
        fig2 = px.pie(values=[row['checked'], row['to_check'] - row['checked']],
                      names=["Проверено", "Осталось"],
                      title="Проверка операций")
        st.plotly_chart(fig2, use_container_width=True)
        st.metric("Процент проверенных транзакций", f"{round(row['checked']/row['to_check']*100, 1)}%")
    else:
        st.info("Нет данных по действиям оператора за сегодня.")

# --- Детализация ---
if selected_transaction_id:
    transaction = fraud_data[fraud_data['transaction_id'] == int(selected_transaction_id)].iloc[0]

    st.markdown("---")
    st.subheader(f"Детализация транзакции ID: {selected_transaction_id}")

    st.markdown("**Информация о клиенте**")
    client_info = pd.read_sql(f"""
        SELECT * FROM clients WHERE client_id = {transaction['client_id']}
    """, engine)
    st.write(client_info.iloc[0].to_dict())

    st.markdown("**Детали операции**")
    transaction_info = pd.read_sql(f"""
        SELECT * FROM transactions WHERE transaction_id = {selected_transaction_id}
    """, engine)
    st.write(transaction_info.iloc[0].to_dict())

    st.markdown("**SHAP-анализ влияющих признаков**")
    shap_df = pd.read_sql(f"""
        SELECT feature_name AS "Признак", shap_value AS "Влияние" 
        FROM shap_values WHERE transaction_id = {selected_transaction_id}
        ORDER BY abs(shap_value) DESC LIMIT 10
    """, engine)

    fig3 = px.bar(shap_df, x="Влияние", y="Признак", orientation='h')
    st.plotly_chart(fig3, use_container_width=True)
